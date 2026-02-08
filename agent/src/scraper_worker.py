"""
Scraper Worker - Processes link jobs and extracts metadata
Story: 2.2 - Universal Link Scraper & Platform Router
"""

import os
import sys
import logging
import hashlib
from typing import Optional
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.scraper.service import ScraperService
from tools.scraper.types import ScraperRequest

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
        required_env_vars = [
            'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY',
            'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER'
        ]
        
        missing = [var for var in required_env_vars if not os.environ.get(var)]
        if missing:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")
        
        logger.info("Initializing ScraperWorker...")
        
        self.supabase: Client = create_client(
            os.environ.get('SUPABASE_URL'),
            os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        self.twilio_client = TwilioClient(
            os.environ.get('TWILIO_ACCOUNT_SID'),
            os.environ.get('TWILIO_AUTH_TOKEN')
        )
        self.twilio_from = os.environ.get('TWILIO_PHONE_NUMBER')
        
        self.scraper_service = ScraperService()
        logger.info("ScraperWorker initialized successfully")

    def fetch_and_lock_link_job(self) -> Optional[dict]:
        """Fetch one pending link job and update to 'processing'."""
        try:
            # We use a simple select/update for now, similar to video_worker
            # In deep production, use the RPC with filter support
            result = self.supabase.table('jobs').select('*').eq(
                'content_type', 'link'
            ).eq(
                'status', 'pending'
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
            
            # 2. Deduplication & Persistence
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            # Check for existing metadata
            existing = self.supabase.table('link_metadata').select('id, scrape_count').eq('url_hash', url_hash).maybe_single().execute()
            
            link_id = None
            if existing.data:
                link_id = existing.data['id']
                # Increment count
                self.supabase.table('link_metadata').update({
                    'scrape_count': (existing.data.get('scrape_count') or 1) + 1,
                    'last_updated_at': 'now()'
                }).eq('id', link_id).execute()
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
                    'scrape_status': 'scraped'
                }).execute()
                
                if insert_result.data:
                    link_id = insert_result.data[0]['id']
                    logger.info(f"Created new metadata {link_id} for {url}")

            # 3. Create User Saved Link entry
            if link_id:
                self.supabase.table('user_saved_links').insert({
                    'link_id': link_id,
                    'user_id': user_phone,
                    'source_channel_id': job.get('source_channel_id', user_phone),
                    'source_type': job.get('source_type', 'dm'),
                    'attributed_user_id': user_phone
                }).execute()

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
            self._mark_failed(job, 'scraping_failed')
            return False

    def notify_user_success(self, to: str, title: str, platform: str):
        """Send a success message via WhatsApp."""
        try:
            if not to.startswith('whatsapp:'):
                to = f"whatsapp:{to}"
            
            # Ensure sender is formatted for WhatsApp if recipient is
            from_number = self.twilio_from
            if to.startswith('whatsapp:') and not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"
            
            msg = f"✅ *Saved to Vault!* \n\n"
            msg += f"📌 *Title:* {title or 'Shared Link'}\n"
            msg += f"🌐 *Platform:* {platform.title()}\n\n"
            msg += f"I've cataloged this for you. You can search for it anytime! 🗃️"
            
            self.twilio_client.messages.create(
                from_=from_number,
                to=to,
                body=msg
            )
            logger.info(f"Success message sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send success message: {e}")

    def _mark_failed(self, job: dict, error_category: str):
        job_id = job['id']
        user_phone = job.get('user_phone') or job['payload'].get('From', '').replace('whatsapp:', '')
        
        self.supabase.table('jobs').update({'status': 'failed'}).eq('id', job_id).execute()
        
        message = self.ERROR_MESSAGES.get(error_category, self.ERROR_MESSAGES['unknown'])
        try:
            # Ensure recipient has whatsapp prefix
            to_number = user_phone
            if not to_number.startswith('whatsapp:'):
                to_number = f"whatsapp:{user_phone}"

            # Ensure sender is formatted for WhatsApp if recipient is
            from_number = self.twilio_from
            if to_number.startswith('whatsapp:') and not from_number.startswith('whatsapp:'):
                from_number = f"whatsapp:{from_number}"

            self.twilio_client.messages.create(
                from_=from_number,
                to=to_number,
                body=f"⚠️ {message}"
            )
        except Exception as e:
            logger.error(f"Failed to notify user of failure: {e}")

    def run_loop(self):
        logger.info("Scraper worker polling started...")
        import time
        while True:
            try:
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
