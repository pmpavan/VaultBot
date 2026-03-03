"""
Scraper Worker - Processes link jobs and extracts metadata
Story: 2.2 - Universal Link Scraper & Platform Router
Story: 2.10.1 - Worker HTTP Framework Migration
"""

import os
import sys
import logging
import hashlib
import signal
from contextlib import asynccontextmanager
from typing import Optional
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from messaging_factory import get_messaging_provider
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.scraper.service import ScraperService
from tools.scraper.types import ScraperRequest
from tools.normalizer.service import NormalizerService
from tools.normalizer.types import NormalizerRequest
from tools.summarizer.service import SummarizerService
from tools.summarizer.types import SummarizerRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Module-level singleton worker — created once at startup, not per-request
_worker: Optional["ScraperWorker"] = None


def _handle_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT at the module level (runs in main thread)."""
    logger.info(f"Received signal {signum}, shutting down...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: initialise the worker once at container startup."""
    global _worker
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)
    _worker = ScraperWorker()
    yield
    # Cleanup (if needed) goes here
    _worker = None


# FastAPI Application
app = FastAPI(title="Scraper Worker", lifespan=lifespan)


class ProcessRequest(BaseModel):
    job_id: str = Field(..., min_length=1, description="The UUID of the job to process")


@app.post("/process")
def process_job(request: ProcessRequest, x_vaultbot_worker_secret: Optional[str] = Header(None)):
    """Webhook endpoint to process a specific job."""
    # Security check
    worker_secret = os.environ.get('WORKER_SECRET')
    if worker_secret and x_vaultbot_worker_secret != worker_secret:
        logger.warning(f"Unauthorized request with secret: {x_vaultbot_worker_secret}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    if _worker is None:
        raise HTTPException(status_code=503, detail="Worker not initialised")
    job = _worker.fetch_and_lock_specific_job(request.job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found or not in pending state")

    success = _worker.process_and_update(job)
    if success:
        return {"status": "success", "job_id": request.job_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to process job")


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
        self.summarizer_service = SummarizerService()

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

    def fetch_and_lock_specific_job(self, job_id: str) -> Optional[dict]:
        """Fetch a specific pending link job by ID and update to 'processing'."""
        try:
            result = self.supabase.table('jobs').select('*').eq(
                'id', job_id
            ).eq(
                'status', 'pending'
            ).limit(1).execute()
            
            if not result.data:
                return None
            
            job = result.data[0]
            
            # Atomic update
            update_result = self.supabase.table('jobs').update({
                'status': 'processing'
            }).eq('id', job_id).eq('status', 'pending').execute()
            
            if update_result.data:
                logger.info(f"Claimed specific link job {job_id}")
                return job
            
            return None
        except Exception as e:
            logger.error(f"Error fetching specific link job {job_id}: {e}")
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
                logger.debug(f"Normalization exception: {e}")
            
            logger.debug(f"normalized_data is {normalized_data}")
            
            # 1.6 Generate AI Summary (Text)
            ai_summary = None
            try:
                sum_req = SummarizerRequest(
                    title=metadata.title,
                    description=metadata.description
                )
                ai_summary = self.summarizer_service.generate_summary(sum_req)
            except Exception as e:
                logger.warning(f"Summarization failed for {url}: {e}")
                
            # 1.7 Visual AI Summary (Video)
            from tools.scraper.types import ContentType
            if metadata.content_type == ContentType.VIDEO:
                try:
                    from tools.video.downloader import SocialVideoDownloader
                    from tools.video.service import VideoProcessingService
                    from tools.video.types import VideoProcessingRequest
                    
                    proxy_url = os.environ.get('PROXY_URL')
                    downloader = SocialVideoDownloader(proxy_url=proxy_url)
                    video_path = downloader.download(url)
                    
                    try:
                        video_service = VideoProcessingService()
                        vid_req = VideoProcessingRequest(
                            video_path=video_path,
                            message_id=job_id
                        )
                        vid_resp = video_service.process_video(vid_req)
                        metadata.visual_summary = vid_resp.summary
                        
                        if ai_summary and metadata.visual_summary:
                            ai_summary = f"{ai_summary}\n\nVisual Analysis: {metadata.visual_summary}"
                        elif metadata.visual_summary:
                            ai_summary = f"Visual Analysis: {metadata.visual_summary}"
                    finally:
                        if os.path.exists(video_path):
                            try:
                                os.unlink(video_path)
                            except OSError:
                                pass
                except Exception as e:
                    logger.warning(f"Video visual extraction failed for {url}: {e}")
                    warning_msg = "⚠️ Visual extraction failed or was blocked by the platform."
                    if ai_summary:
                        ai_summary = f"{ai_summary}\n\n{warning_msg}"
                    else:
                        ai_summary = warning_msg
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
                        'normalized_tags': normalized_data.tags,
                        'ai_summary': ai_summary
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
                    'normalized_tags': normalized_data.tags if normalized_data else None,
                    'ai_summary': ai_summary
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
            msg = f"✅ Successfully saved: {title or 'Link'} from {platform or 'Unknown'}"
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


