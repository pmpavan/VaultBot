"""
Image Worker - Processes image jobs and extracts content summaries
Story: 2.4 - Image Post Extraction
"""

import os
import sys
import logging
import signal
from typing import Optional, Dict, Any
from supabase import create_client, Client
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from messaging_factory import get_messaging_provider

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nodes.image_processor import ImageProcessorNode, ImageProcessorState
from tools.normalizer.service import NormalizerService
from tools.normalizer.types import NormalizerRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageWorker:
    """Worker that processes image jobs and extracts content summaries."""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        'download_failed': "Sorry, we couldn't download your images. Please try sending them again.",
        'processing_failed': "We had trouble processing your images. Please try different images.",
        'network_error': "We're having trouble connecting. Please try again in a few moments.",
        'unknown': "Something went wrong processing your images. Our team has been notified."
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
        
        logger.info("Initializing ImageWorker...")
        
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
        
        # Initialize Messaging Provider
        try:
            self.messaging = get_messaging_provider()
            logger.info("Messaging provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize messaging provider: {e}")
            raise
        
        # Initialize image processor graph
        from nodes.image_processor import create_image_processor_graph
        self.image_processor = create_image_processor_graph()
        self.normalizer_service = NormalizerService()
        
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
    def fetch_and_lock_image_job(self) -> Optional[dict]:
        """
        Fetch one pending image job and atomically update to 'processing'.
        Retries on transient network errors.
        
        Returns:
            Job record if found, None otherwise
        """
        try:
            # Fetch pending image jobs
            result = self.supabase.table('jobs').select('*').eq(
                'content_type', 'image'
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
                logger.info(f"Claimed image job {job_id} for processing")
                return job
            
            # Another worker claimed it
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching image job: {e}")
            raise
    
    def process_and_update(self, job: dict) -> bool:
        """
        Process image job and update database with results.
        
        Args:
            job: Job record from database
            
        Returns:
            True if successful, False if failed
        """
        job_id = job['id']
        
        try:
            # Extract payload
            payload = job['payload']
            logger.debug(f"Processing image job {job_id}")
            
            # Get URL from payload (could be Twilio MediaUrl or a Social Media Link)
            url = None
            
            # Case 1: Social Media Link (from text message)
            if 'Body' in payload:
                # Simple extraction, assumes classifier validated this is an image link
                # In real flow, classifier might put URL in a specific field
                # But here we assume Body contains the URL
                url = payload['Body'].strip()
                
            # Case 2: Twilio Media Attachment (MMS/WhatsApp Image)
             # Check up to 10 media items
            for i in range(10): 
                media_key = f'MediaUrl{i}' if i > 0 else 'MediaUrl0'
                if media_key in payload:
                    url = payload[media_key]
                    break
            
            if not url:
                raise ValueError("No URL found in payload")
            
            # Determine platform hint from classifier??
            # The job table might have metadata, but for now we rely on extractor service detection
            platform_hint = None
            
            # Create state for image processor node
            state: ImageProcessorState = {
                'job_id': job_id,
                'url': url,
                'message_id': payload.get('MessageSid', job_id),
                'platform_hint': platform_hint,
                'image_summary': None,
                'metadata': None,
                'error': None
            }
            
            # Process image
            logger.info(f"Processing image for job {job_id}")
            # Invoke the graph - returns the final state
            result_state = self.image_processor.invoke(state)
            
            # Check for errors
            if result_state.get('error'):
                raise Exception(result_state['error'])
            
            image_summary = result_state.get('image_summary')
            if not image_summary:
                raise Exception("No image summary generated")
            
            logger.info(f"Image job {job_id} processed successfully")

            # --- Normalize Data ---
            normalized_data = None
            try:
                metadata_caption = result_state.get('metadata', {}).get('caption') if result_state.get('metadata') else None
                norm_req = NormalizerRequest(
                    title=metadata_caption or "Image Analysis",
                    description=image_summary,
                    raw_content=None,
                    source_url=url
                )
                normalized_data = self.normalizer_service.normalize(norm_req)
            except Exception as e:
                logger.warning(f"Normalization failed for image {url}: {e}")
            
            # --- Data Persistence Start ---
            import hashlib
            
            # Generate a consistent hash for the image URL to handle deduplication
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            # Check for existing metadata
            existing = self.supabase.table('link_metadata').select('id, scrape_count').eq('url_hash', url_hash).limit(1).execute()
            
            link_id = None
            if existing and existing.data and len(existing.data) > 0:
                link_id = existing.data[0]['id']
                # Increment count
                # Prepare update data
                update_data = {
                    'scrape_count': (existing.data[0].get('scrape_count') or 1) + 1,
                    'last_updated_at': 'now()'
                }

                if normalized_data:
                    update_data.update({
                        'normalized_category': normalized_data.category.value,
                        'normalized_price_range': normalized_data.price_range.value if normalized_data.price_range else None,
                        'normalized_tags': normalized_data.tags
                    })

                self.supabase.table('link_metadata').update(update_data).eq('id', link_id).execute()
                logger.info(f"Re-used existing image metadata {link_id}")
            else:
                # Insert new metadata
                metadata = result_state.get('metadata') or {}
                
                insert_result = self.supabase.table('link_metadata').insert({
                    'url': url,
                    'url_hash': url_hash,
                    'platform': metadata.get('platform', 'unknown'),
                    'content_type': 'image',
                    'extraction_strategy': 'vision',
                    'title': metadata.get('caption', 'Image Analysis')[:255] if metadata.get('caption') else 'Image Analysis',
                    'description': image_summary, 
                    'author': metadata.get('author'),
                    'thumbnail_url': metadata.get('image_urls', [None])[0] if metadata.get('image_urls') else None,
                    'thumbnail_url': metadata.get('image_urls', [None])[0] if metadata.get('image_urls') else None,
                    'scrape_status': 'scraped',
                    'normalized_category': normalized_data.category.value if normalized_data else None,
                    'normalized_price_range': normalized_data.price_range.value if normalized_data and normalized_data.price_range else None,
                    'normalized_tags': normalized_data.tags if normalized_data else None
                }).execute()
                
                if insert_result.data:
                    link_id = insert_result.data[0]['id']
                    logger.info(f"Created new image metadata {link_id}")

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
                logger.info(f"Linked image {link_id} to user {user_phone}")
            # --- Data Persistence End ---

            # Update job with results
            result_data = {
                'image_summary': image_summary,
                'content_type': 'image',
                'link_id': link_id
            }
            if result_state.get('metadata'):
                result_data['metadata'] = result_state['metadata']
                
            self.supabase.table('jobs').update({
                'result': result_data,
                'status': 'complete'
            }).eq('id', job_id).execute()
            
            logger.info(f"Job {job_id} successfully completed and updated")
            
            # Notify User
            user_phone_notify = payload.get('From', '')
            if user_phone_notify:
                self.notify_user_success(user_phone_notify, "Image Analysis")
                
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
            self.messaging.send_message(to=to, body=msg)
            logger.info(f"Success message sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send success message: {e}")
    
    def _mark_job_failed(self, job: dict, error_category: str):
        """Mark job as failed and notify user."""
        job_id = job['id']
        
        try:
            self.supabase.table('jobs').update({
                'status': 'failed'
            }).eq('id', job_id).execute()
            
            logger.warning(f"Job {job_id} marked as failed (category: {error_category})")
            
            self.notify_user_failure(job, error_category)
            
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=False
    )
    def notify_user_failure(self, job: dict, error_category: str):
        """Notify user via WhatsApp about processing failure."""
        try:
            payload = job['payload']
            user_phone = payload.get('From', '')
            
            if not user_phone:
                logger.warning(f"No phone number found in job {job['id']} payload")
                return
            
            # Ensure recipient has whatsapp prefix if needed (though payload usually has it)
            self.messaging.send_message(to=user_phone, body=f"⚠️ {message}")
            
            logger.info(f"Sent failure notification to {user_phone} for job {job['id']}")
            
        except Exception as e:
            logger.error(f"Failed to send notification for job {job['id']}: {e}")
    
    def process_one_job(self) -> bool:
        """Process one image job from the queue."""
        try:
            job = self.fetch_and_lock_image_job()
            
            if not job:
                return False
            
            self.process_and_update(job)
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in process_one_job: {e}", exc_info=True)
            return False
    
    def run_loop(self, max_iterations: Optional[int] = None):
        """Run worker loop to process image jobs."""
        logger.info(f"Starting image worker loop (max_iterations={max_iterations})")
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
                import time
                logger.debug("No image jobs available, sleeping for 5 seconds")
                time.sleep(5)
            
            iteration += 1


if __name__ == '__main__':
    try:
        worker = ImageWorker()
        worker.run_loop()
    except KeyboardInterrupt:
        logger.info("Image worker stopped by user")
    except Exception as e:
        logger.critical(f"Image worker crashed: {e}", exc_info=True)
        sys.exit(1)
