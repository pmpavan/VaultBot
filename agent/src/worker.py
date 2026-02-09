"""
Classifier Worker - Processes pending jobs and classifies content
Story: 1.3 - Payload Parser & Classification
"""

import os
import sys
import logging
import signal
from typing import Optional
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nodes.classifier import create_classifier_graph, ClassifierState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClassifierWorker:
    """Worker that processes pending jobs and classifies their content."""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        'unsupported_media': "Sorry, we don't support this type of media yet. Please send a link, image, or video.",
        'network_error': "We're having trouble connecting. Please try again in a few moments.",
        'unknown': "Something went wrong processing your message. Our team has been notified."
    }
    
    def __init__(self):
        """Initialize Supabase and Twilio clients with validation."""
        # Validate required environment variables
        required_env_vars = {
            'SUPABASE_URL': 'Supabase project URL',
            'SUPABASE_SERVICE_ROLE_KEY': 'Supabase service role key',
            'TWILIO_ACCOUNT_SID': 'Twilio account SID',
            'TWILIO_AUTH_TOKEN': 'Twilio auth token',
            'TWILIO_PHONE_NUMBER': 'Twilio phone number'
        }
        
        missing = []
        for var, description in required_env_vars.items():
            if not os.environ.get(var):
                missing.append(f"{var} ({description})")
        
        if missing:
            error_msg = f"Missing required environment variables:\n" + "\n".join(f"  - {m}" for m in missing)
            logger.error(error_msg)
            raise EnvironmentError(error_msg)
        
        logger.info("Initializing ClassifierWorker...")
        
        # Initialize Supabase client
        try:
            self.supabase: Client = create_client(
                os.environ.get('SUPABASE_URL'),
                os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
        
        # Initialize Twilio client
        try:
            self.twilio_client = TwilioClient(
                os.environ.get('TWILIO_ACCOUNT_SID'),
                os.environ.get('TWILIO_AUTH_TOKEN')
            )
            self.twilio_from = os.environ.get('TWILIO_PHONE_NUMBER')
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise
        
        # Initialize classifier graph
        self.classifier_graph = create_classifier_graph()
        
        # Shutdown flag
        self.shutdown_requested = False
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, scheduling shutdown...")
        self.shutdown_requested = True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def fetch_and_lock_job(self) -> Optional[dict]:
        """
        Fetch one pending job and atomically update to 'processing'.
        Retries on transient network errors.
        
        Returns:
            Job record if found, None otherwise
        """
        try:
            # Atomic pick: SELECT FOR UPDATE SKIP LOCKED pattern
            result = self.supabase.rpc(
                'claim_pending_job',
                {}
            ).execute()
            
            if result.data and len(result.data) > 0:
                job = result.data[0]
                logger.info(f"Claimed job {job['id']} for processing")
                return job
            
            return None
        except Exception as e:
            logger.warning(f"Error fetching job: {e}")
            raise
    
    def classify_and_update(self, job: dict) -> bool:
        """
        Classify job content and update database.
        
        Args:
            job: Job record from database
            
        Returns:
            True if successful, False if failed
        """
        job_id = job['id']
        
        try:
            # Extract payload
            payload = job['payload']
            logger.debug(f"Processing job {job_id} with payload: {payload}")
            
            # Create state for classifier
            state: ClassifierState = {
                'job_id': job_id,
                'payload': payload,
                'content_type': None,
                'platform': None,
                'error': None
            }
            
            # Classify content using graph
            result_state = self.classifier_graph.invoke(state)
            
            if result_state.get('error'):
                raise Exception(result_state['error'])
            
            content_type = result_state['content_type']
            platform = result_state['platform']
            
            logger.info(f"Job {job_id} classified as {content_type} / {platform}")
            
            # Update job with classification
            self.supabase.table('jobs').update({
                'content_type': content_type,
                'platform': platform,
                'status': 'pending'  # Ready for next processing node
            }).eq('id', job_id).execute()
            
            logger.info(f"Job {job_id} successfully classified and updated")
            return True
            
        except KeyError as e:
            logger.error(f"Missing required field in job {job_id}: {e}")
            self._mark_job_failed(job, 'unsupported_media')
            return False
            
        except Exception as e:
            logger.error(f"Classification error for job {job_id}: {e}", exc_info=True)
            self._mark_job_failed(job, 'unknown')
            return False
    
    def _mark_job_failed(self, job: dict, error_category: str):
        """
        Mark job as failed and notify user.
        
        Args:
            job: Job record
            error_category: Category of error for user-friendly message
        """
        job_id = job['id']
        
        try:
            # Mark as failed
            self.supabase.table('jobs').update({
                'status': 'failed'
            }).eq('id', job_id).execute()
            
            logger.warning(f"Job {job_id} marked as failed (category: {error_category})")
            
            # Notify user
            self.notify_user_failure(job, error_category)
            
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=False
    )
    def notify_user_failure(self, job: dict, error_category: str):
        """
        Notify user via WhatsApp about processing failure.
        Retries once on failure, but doesn't raise if notification fails.
        
        Args:
            job: Job record
            error_category: Category of error for user-friendly message
        """
        try:
            payload = job['payload']
            user_phone = payload.get('From', '')
            
            if not user_phone:
                logger.warning(f"No phone number found in job {job['id']} payload")
                return
            
            # Ensure recipient has whatsapp prefix if needed (though payload usually has it)
            if not user_phone.startswith('whatsapp:') and len(user_phone) > 10:
                 # heuristic: if it looks like a phone number but missing prefix
                 user_phone = f"whatsapp:{user_phone}"

            # Ensure sender is formatted for WhatsApp if recipient is
            from_number = self.twilio_from
            if user_phone.startswith('whatsapp:') and not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            
            # Get user-friendly message
            message = self.ERROR_MESSAGES.get(error_category, self.ERROR_MESSAGES['unknown'])
            
            self.twilio_client.messages.create(
                from_=from_number,
                to=user_phone,
                body=f"⚠️ {message}"
            )
            
            logger.info(f"Sent failure notification to {user_phone} for job {job['id']}")
            
        except Exception as e:
            logger.error(f"Failed to send notification for job {job['id']}: {e}")
            # Don't raise - notification failure shouldn't crash the worker
    
    def process_one_job(self) -> bool:
        """
        Process one job from the queue.
        
        Returns:
            True if a job was processed, False if queue is empty
        """
        try:
            job = self.fetch_and_lock_job()
            
            if not job:
                return False
            
            self.classify_and_update(job)
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in process_one_job: {e}", exc_info=True)
            return False
    
    def run_loop(self, max_iterations: Optional[int] = None):
        """
        Run worker loop to process jobs.
        
        Args:
            max_iterations: Maximum number of iterations (None for infinite)
        """
        logger.info(f"Starting worker loop (max_iterations={max_iterations})")
        iteration = 0
        
        while not self.shutdown_requested:
            if max_iterations and iteration >= max_iterations:
                logger.info(f"Reached max iterations ({max_iterations}), stopping")
                break
            
            if self.shutdown_requested:
                logger.info("Shutdown requested, stopping loop")
                break
            
            processed = self.process_one_job()
            
            if not processed:
                # No jobs available, wait before retrying
                import time
                logger.debug("No jobs available, sleeping for 5 seconds")
                time.sleep(5)
            
            iteration += 1


if __name__ == '__main__':
    try:
        worker = ClassifierWorker()
        worker.run_loop()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.critical(f"Worker crashed: {e}", exc_info=True)
        sys.exit(1)
