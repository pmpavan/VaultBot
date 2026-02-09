"""
Video Worker - Processes video jobs and extracts content summaries
Story: 2.3 - Video Frame Extraction
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

from nodes.video_processor import create_video_processor_graph, VideoProcessorState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoWorker:
    """Worker that processes video jobs and extracts content summaries."""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        'download_failed': "Sorry, we couldn't download your video. Please try sending it again.",
        'processing_failed': "We had trouble processing your video. Please try a different video.",
        'network_error': "We're having trouble connecting. Please try again in a few moments.",
        'unknown': "Something went wrong processing your video. Our team has been notified."
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
        
        logger.info("Initializing VideoWorker...")
        
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
        
        # Initialize video processor graph
        self.video_processor_graph = create_video_processor_graph(num_frames=5)
        
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
    def fetch_and_lock_video_job(self) -> Optional[dict]:
        """
        Fetch one pending video job and atomically update to 'processing'.
        Retries on transient network errors.
        
        Returns:
            Job record if found, None otherwise
        """
        try:
            # Fetch pending video jobs
            result = self.supabase.table('jobs').select('*').eq(
                'content_type', 'video'
            ).eq(
                'status', 'pending'
            ).limit(1).execute()
            
            if not result.data or len(result.data) == 0:
                return None
            
            job = result.data[0]
            job_id = job['id']
            
            # Atomically update to processing
            update_result = self.supabase.table('jobs').update({
                'status': 'processing'
            }).eq('id', job_id).eq('status', 'pending').execute()
            
            # Check if we successfully claimed the job
            if update_result.data and len(update_result.data) > 0:
                logger.info(f"Claimed video job {job_id} for processing")
                return job
            
            # Another worker claimed it
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching video job: {e}")
            raise
    
    def process_and_update(self, job: dict) -> bool:
        """
        Process video job and update database with results.
        
        Args:
            job: Job record from database
            
        Returns:
            True if successful, False if failed
        """
        job_id = job['id']
        
        try:
            # Extract payload
            payload = job['payload']
            logger.debug(f"Processing video job {job_id}")
            
            # Get video URL from payload
            # Twilio sends video as MediaUrl0, MediaUrl1, etc.
            video_url = None
            for i in range(10):  # Check up to 10 media items
                media_key = f'MediaUrl{i}' if i > 0 else 'MediaUrl0'
                if media_key in payload:
                    video_url = payload[media_key]
                    break
            
            if not video_url:
                raise ValueError("No video URL found in payload")
            
            # Get Twilio auth token for video download
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            
            # Create state for video processor node
            state: VideoProcessorState = {
                'job_id': job_id,
                'video_url': video_url,
                'message_id': payload.get('MessageSid', job_id),
                'auth_token': auth_token,
                'account_sid': self.twilio_client.account_sid,
                'video_summary': None,
                'error': None
            }
            
            # Process video
            logger.info(f"Processing video for job {job_id}")
            result_state = self.video_processor_graph.invoke(state)
            
            # Check for errors
            if result_state.get('error'):
                raise Exception(result_state['error'])
            
            video_summary = result_state.get('video_summary')
            if not video_summary:
                raise Exception("No video summary generated")
            
            logger.info(f"Video job {job_id} processed successfully")
            
            # --- Data Persistence Start ---
            import hashlib
            
            # Generate a consistent hash for the video URL to handle deduplication
            # In a real-world scenario, we might use a hash of the file content, 
            # but for now, the URL (or MediaSid) is the best proxy.
            url_hash = hashlib.sha256(video_url.encode()).hexdigest()
            
            # Check for existing metadata
            existing = self.supabase.table('link_metadata').select('id, scrape_count').eq('url_hash', url_hash).limit(1).execute()
            
            link_id = None
            if existing and existing.data and len(existing.data) > 0:
                link_id = existing.data[0]['id']
                # Increment count
                self.supabase.table('link_metadata').update({
                    'scrape_count': (existing.data[0].get('scrape_count') or 1) + 1,
                    'last_updated_at': 'now()'
                }).eq('id', link_id).execute()
                logger.info(f"Re-used existing video metadata {link_id}")
            else:
                # Insert new metadata
                # We store the video summary in the 'description' field or a structured content field
                insert_result = self.supabase.table('link_metadata').insert({
                    'url': video_url,
                    'url_hash': url_hash,
                    'platform': 'whatsapp_video', # specialized platform type
                    'content_type': 'video',
                    'extraction_strategy': 'vision',
                    'title': 'Video Analysis', # Placeholder title
                    'description': video_summary, # The generated summary goes here
                    'thumbnail_url': None, # We could upload a frame here in the future
                    'scrape_status': 'scraped'
                }).execute()
                
                if insert_result.data:
                    link_id = insert_result.data[0]['id']
                    logger.info(f"Created new video metadata {link_id}")

            # Create User Saved Link entry
            user_phone = payload.get('From', '').replace('whatsapp:', '')
            if link_id and user_phone:
                # Use source_channel_id if present (group), otherwise user_phone (dm)
                source_channel_id = job.get('source_channel_id') or user_phone
                source_type = job.get('source_type') or 'dm'
                
                self.supabase.table('user_saved_links').insert({
                    'link_id': link_id,
                    'user_id': user_phone,
                    'source_channel_id': source_channel_id,
                    'source_type': source_type,
                    'attributed_user_id': user_phone
                }).execute()
                logger.info(f"Linked video {link_id} to user {user_phone}")
            # --- Data Persistence End ---

            # Update job with results
            self.supabase.table('jobs').update({
                'result': {
                    'video_summary': video_summary,
                    'content_type': 'video',
                    'link_id': link_id
                },
                'status': 'complete'
            }).eq('id', job_id).execute()
            
            logger.info(f"Job {job_id} successfully completed and updated")
            
            # 5. Notify User
            user_phone_notify = payload.get('From', '')
            if user_phone_notify:
                self.notify_user_success(user_phone_notify, "Video Analysis")
                
            return True
            
        except ValueError as e:
            logger.error(f"Invalid payload for job {job_id}: {e}")
            self._mark_job_failed(job, 'processing_failed')
            return False
            
        except Exception as e:
            logger.error(f"Processing error for job {job_id}: {e}", exc_info=True)
            
            # Categorize error
            error_str = str(e).lower()
            if 'download' in error_str or 'network' in error_str:
                error_category = 'download_failed'
            else:
                error_category = 'processing_failed'
            
            self._mark_job_failed(job, error_category)
            return False

    def notify_user_success(self, to: str, title: str):
        """Send a success message via WhatsApp."""
        try:
            if not to.startswith('whatsapp:'):
                to = f"whatsapp:{to}"
            
            # Ensure sender is formatted for WhatsApp if recipient is
            from_number = self.twilio_from
            if to.startswith('whatsapp:') and not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            
            msg = f"✅ *Video Processed!* \n\n"
            msg += f"Your video has been analyzed and the summary is ready in your Vault. 🎥"
            
            self.twilio_client.messages.create(
                from_=from_number,
                to=to,
                body=msg
            )
            logger.info(f"Success message sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send success message: {e}")
    
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
        Process one video job from the queue.
        
        Returns:
            True if a job was processed, False if queue is empty
        """
        try:
            job = self.fetch_and_lock_video_job()
            
            if not job:
                return False
            
            self.process_and_update(job)
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in process_one_job: {e}", exc_info=True)
            return False
    
    def run_loop(self, max_iterations: Optional[int] = None):
        """
        Run worker loop to process video jobs.
        
        Args:
            max_iterations: Maximum number of iterations (None for infinite)
        """
        logger.info(f"Starting video worker loop (max_iterations={max_iterations})")
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
                logger.debug("No video jobs available, sleeping for 5 seconds")
                time.sleep(5)
            
            iteration += 1


if __name__ == '__main__':
    try:
        worker = VideoWorker()
        worker.run_loop()
    except KeyboardInterrupt:
        logger.info("Video worker stopped by user")
    except Exception as e:
        logger.critical(f"Video worker crashed: {e}", exc_info=True)
        sys.exit(1)
