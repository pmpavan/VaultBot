"""
Scraper Worker - Processes link jobs and extracts metadata
Story: 2.2 - Universal Link Scraper & Platform Router
"""

import os
import sys
import logging
import hashlib
import signal
from typing import Optional
from supabase import create_client, Client
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from messaging_factory import get_messaging_provider

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.scraper.service import ScraperService
from tools.scraper.types import ScraperRequest
from agent.src.tools.normalizer.service import NormalizerService
from agent.src.tools.normalizer.types import NormalizerRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperWorker:
    """Worker that processes link jobs and extracts metadata."""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        'scraping_failed': "Sorry, we couldn't extract info from that link. Please try another one.",
        'network_error': "We're having trouble connecting. Please try again in a few moments.",
        'unknown': "Something went wrong processing your link. Our team has been notified."
    }
    
    def __init__(self):
        """Initialize Supabase, Twilio, and Scraper service."""
        if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_SERVICE_ROLE_KEY'):
            logger.error("Missing required environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)")
            raise EnvironmentError("Missing required environment variables")
        
        logger.info("Initializing ScraperWorker...")
        
        self.supabase: Client = create_client(
            os.environ.get('SUPABASE_URL'),
            os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        self.messaging = get_messaging_provider()
        
        self.scraper_service = ScraperService()
        self.normalizer_service = NormalizerService()
        
        # Shutdown flag
        self.shutdown_requested = False
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        logger.info("ScraperWorker initialized successfully")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, scheduling shutdown...")
        self.shutdown_requested = True

    def fetch_and_lock_link_job(self) -> Optional[dict]:
        """Fetch one pending link job and update to 'processing'."""
        try:
            # We use a simple select/update for now, similar to video_worker
            # In deep production, use the RPC with filter support
            result = self.supabase.table('jobs').select('*').eq(
                'content_type', 'link'
            ).eq(
                'status', 'pending'
            ).neq(
                'platform', 'generic'
            ).order('created_at').limit(1).execute()
            
            if not result.data:
                return None
            
            job = result.data[0]
            job_id = job['id']
            
            # Atomic update
            update_result = self.supabase.table('jobs').update({
                'status': 'processing'
            }).eq('id', job_id).eq('status', 'pending').execute()
            
            if update_result.data:
                logger.info(f"Claimed link job {job_id}")
                return job
            
            return None
        except Exception as e:
            logger.error(f"Error fetching link job: {e}")
            return None

    def process_and_update(self, job: dict) -> bool:
        """Process link job, save to link_metadata, and notify user."""
        job_id = job['id']
        payload = job['payload']
        url = payload.get('Body', '').strip()
        user_phone = job.get('user_phone') or payload.get('From', '').replace('whatsapp:', '')
        
        if not url:
            logger.error(f"No URL in job {job_id}")
            self._mark_failed(job, 'scraping_failed')
            return False

        try:
            logger.info(f"Scraping URL: {url} for job {job_id}")
            
            # 1. Scrape Metadata
            request = ScraperRequest(url=url)
            metadata = self.scraper_service.scrape(request)

            # 1.5 Normalize Data
            normalized_data = None
            try:
                norm_req = NormalizerRequest(
                    title=metadata.title or "Untitled",
                    description=metadata.description,
                    raw_content=None, # Scraper service doesn't return raw content yet, could add later
                    source_url=url
                )
                normalized_data = self.normalizer_service.normalize(norm_req)
            except Exception as e:
                logger.warning(f"Normalization failed for {url}: {e}")
                print(f"DEBUG: Normalization exception: {e}")
            
            print(f"DEBUG: normalized_data is {normalized_data}")
            
            # 2. Deduplication & Persistence
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            # Check for existing metadata
            existing = self.supabase.table('link_metadata').select('id, scrape_count').eq('url_hash', url_hash).limit(1).execute()
            
            link_id = None
            if existing and existing.data and len(existing.data) > 0:
                link_id = existing.data[0]['id']
                # Increment count
                update_data = {
                    'scrape_count': (existing.data[0].get('scrape_count') or 1) + 1,
                    'last_updated_at': 'now()'
                }
                # Update normalized fields if they were missing or we have new extraction
                if normalized_data:
                    update_data.update({
                        'normalized_category': normalized_data.category.value,
                        'normalized_price_range': normalized_data.price_range.value if normalized_data.price_range else None,
                        'normalized_tags': normalized_data.tags
                    })

                self.supabase.table('link_metadata').update(update_data).eq('id', link_id).execute()
                logger.info(f"Re-used existing metadata {link_id} for {url}")
            else:
                # Insert new metadata
                insert_result = self.supabase.table('link_metadata').insert({
                    'url': url,
                    'url_hash': url_hash,
                    'platform': metadata.platform,
                    'content_type': metadata.content_type,
                    'extraction_strategy': metadata.extraction_strategy,
                    'title': metadata.title,
                    'description': metadata.description,
                    'author': metadata.author,
                    'thumbnail_url': metadata.thumbnail_url,
                    'scrape_status': 'scraped',
                    'normalized_category': normalized_data.category.value if normalized_data else None,
                    'normalized_price_range': normalized_data.price_range.value if normalized_data and normalized_data.price_range else None,
                    'normalized_tags': normalized_data.tags if normalized_data else None
                }).execute()
                
                if insert_result.data:
                    link_id = insert_result.data[0]['id']
                    logger.info(f"Created new metadata {link_id} for {url}")

            # 3. Create User Saved Link entry
            if link_id:
                try:
                    self.supabase.table('user_saved_links').insert({
                        'link_id': link_id,
                        'user_id': user_phone,
                        'source_channel_id': job.get('source_channel_id', user_phone),
                        'source_type': job.get('source_type', 'dm'),
                        'attributed_user_id': user_phone
                    }).execute()
                except Exception as e:
                    # Handle duplicate - user already saved this link
                    if '23505' in str(e) or 'duplicate key' in str(e).lower():
                        logger.info(f"User {user_phone} already saved link {link_id}, treating as success")
                    else:
                        raise  # Re-raise if it's not a duplicate error


            # 4. Finalize Job
            self.supabase.table('jobs').update({
                'status': 'complete',
                'result': {
                    'link_id': link_id,
                    'title': metadata.title,
                    'platform': metadata.platform
                }
            }).eq('id', job_id).execute()

            # 5. Notify User
            self.notify_user_success(user_phone, metadata.title, metadata.platform)
            return True

        except Exception as e:
            logger.error(f"Detailed error in scraper worker for {job_id}: {e}", exc_info=True)
            self._mark_failed(job, 'scraping_failed', error_details=str(e))
            return False

    def notify_user_success(self, to: str, title: str, platform: str):
        """Send a success message via WhatsApp."""
        try:
            if not to.startswith('whatsapp:'):
                to = f"whatsapp:{to}"
            
            # Ensure sender is formatted for WhatsApp if recipient is
            self.messaging.send_message(to=to, body=msg)
        except Exception as e:
            logger.error(f"Failed to send success message: {e}")

    def _mark_failed(self, job: dict, error_category: str, error_details: str = None):
        job_id = job['id']
        user_phone = job.get('user_phone') or job['payload'].get('From', '').replace('whatsapp:', '')
        
        # Include error details in result for debugging
        result_data = {
            'error_category': error_category,
            'error_message': self.ERROR_MESSAGES.get(error_category, self.ERROR_MESSAGES['unknown'])
        }
        if error_details:
            result_data['error_details'] = str(error_details)
            
        self.supabase.table('jobs').update({
            'status': 'failed',
            'result': result_data
        }).eq('id', job_id).execute()
        
        message = self.ERROR_MESSAGES.get(error_category, self.ERROR_MESSAGES['unknown'])
        try:
            # Ensure recipient has whatsapp prefix
            self.messaging.send_message(to=user_phone, body=f"⚠️ {message}")
        except Exception as e:
            logger.error(f"Failed to notify user of failure: {e}")

    def run_loop(self):
        logger.info("Scraper worker polling started...")
        import time
        logger.info("Scraper worker polling started...")
        import time
        while not self.shutdown_requested:
            try:
                if self.shutdown_requested:
                    logger.info("Shutdown requested, stopping loop")
                    break
                
                processed = False
                job = self.fetch_and_lock_link_job()
                if job:
                    self.process_and_update(job)
                    processed = True
                
                if not processed:
                    time.sleep(5)
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(10)

if __name__ == '__main__':
    worker = ScraperWorker()
    worker.run_loop()
