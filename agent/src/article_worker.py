"""
Article Worker - Processes link jobs and extracts article content.
Story: 2.5 - Text Article Parser
Story: 2.10.1 - Worker HTTP Framework Migration
"""

import os
import sys
import logging
import signal
import json
import hashlib
from contextlib import asynccontextmanager
from typing import Optional, Any
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from messaging_factory import get_messaging_provider
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from nodes.article_processor import create_article_processor_graph, ArticleProcessorState
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
_worker: Optional["ArticleWorker"] = None


def _handle_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT at the module level (runs in main thread)."""
    logger.info(f"Received signal {signum}, shutting down...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: initialise the worker once at container startup."""
    global _worker
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)
    _worker = ArticleWorker()
    yield
    _worker = None


# FastAPI Application
app = FastAPI(title="Article Worker", lifespan=lifespan)


class ProcessRequest(BaseModel):
    job_id: str = Field(..., min_length=1, description="The UUID of the job to process")


@app.post("/process")
def process_job(request: ProcessRequest, x_vaultbot_worker_secret: Optional[str] = Header(None)):
    """Webhook endpoint to process a specific article job."""
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

    success = _worker.process_job(job)
    if success:
        return {"status": "success", "job_id": request.job_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to process job")


class ArticleWorker:
    """Worker that processes link jobs and extracts article content."""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        'extraction_failed': "Sorry, we couldn't read that article. It might be paywalled or inaccessible.",
        'network_error': "We're having trouble connecting to the link. Please try again in a few moments.",
        'unknown': "Something went wrong processing your link. Our team has been notified."
    }
    
    def __init__(self):
        """Initialize Supabase and Twilio clients with validation."""
        required_env_vars = [
            'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        missing = [var for var in required_env_vars if not os.environ.get(var)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
        
        logger.info("Initializing ArticleWorker...")
        
        # Initialize Clients
        self.supabase: Client = create_client(
            os.environ['SUPABASE_URL'],
            os.environ['SUPABASE_SERVICE_ROLE_KEY']
        )
        
        self.messaging = get_messaging_provider()

        # Initialize Processor Graph
        self.article_processor = create_article_processor_graph()
        self.normalizer_service = NormalizerService()
        self.summarizer_service = SummarizerService()

        logger.info("ArticleWorker initialized successfully")
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def fetch_and_lock_job(self) -> Optional[dict]:
        """Fetch and lock a pending link job."""
        try:
            # Fetch pending link jobs
            # Note: We look for content_type='link' which typically means a generic URL
            # The scraper worker might handle specific social media links (e.g., youtube)
            result = self.supabase.table('jobs').select('*').eq(
                'content_type', 'link'
            ).eq(
                'status', 'pending'
            ).eq(
                'platform', 'generic'
            ).limit(1).execute()
            
            if not result.data:
                return None
            
            job = result.data[0]
            job_id = job['id']
            
            # Atomically lock job
            update = self.supabase.table('jobs').update({
                'status': 'processing'
            }).eq('id', job_id).eq('status', 'pending').execute()
            
            if update.data:
                logger.info(f"Claimed article job {job_id}")
                return job
                
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching job: {e}")
            raise

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
            update = self.supabase.table('jobs').update({
                'status': 'processing'
            }).eq('id', job_id).eq('status', 'pending').execute()
            
            if update.data:
                logger.info(f"Claimed specific article job {job_id}")
                return job
                
            return None
        except Exception as e:
            logger.error(f"Error fetching specific article job {job_id}: {e}")
            return None

    def process_job(self, job: dict) -> bool:
        """Process a single job."""
        job_id = job['id']
        logger.info(f"Processing job {job_id}")
        
        try:
            payload = job['payload']
            url = None
            
            # Extract URL from payload
            # Assuming 'Body' contains the URL for now, or fields parsed by classifier
            if 'Body' in payload:
                url = payload['Body'].strip()
            # If classifier parsed it into a specific field in payload, could use that
            # For robustness, we check if 'url' key exists in payload
            if job.get('result') and isinstance(job['result'], dict) and job['result'].get('url'):
                 url = job['result']['url']

            if not url:
                # Basic URL extraction from body if not structured
                import re
                urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', payload.get('Body', ''))
                if urls:
                    url = urls[0]

            if not url:
                raise ValueError("No URL found in job payload")
                
            # Create State
            state: ArticleProcessorState = {
                'job_id': job_id,
                'url': url,
                'content_type_hint': None, # Let classifier decide
                'text': None,
                'title': None,
                'author': None,
                'publish_date': None,
                'site_name': None,
                'metadata': None,
                'og_tags': None,
                'content_type': 'generic',
                'is_paywall': False,
                'error': None
            }
            
            # Execute Processor
            result_state = self.article_processor.invoke(state)
            
            if result_state.get('error'):
                if not result_state.get('text'):
                    # Only fail if no text extracted at all
                    raise Exception(result_state['error'])
                else:
                    logger.warning(f"Partial error in job {job_id}: {result_state['error']}")

            # Normalize Data
            normalized_data = None
            try:
                # Truncate text for normalization to avoid massive tokens
                content_text = result_state.get('text', '') or ''
                norm_req = NormalizerRequest(
                    title=result_state.get('title') or "Untitled",
                    description=result_state.get('og_tags', {}).get('description'),
                    raw_content=content_text[:5000], 
                    source_url=url
                )
                normalized_data = self.normalizer_service.normalize(norm_req)
            except Exception as e:
                logger.warning(f"Normalization failed for article {url}: {e}")

            # Generate AI Summary
            ai_summary = None
            try:
                content_text = result_state.get('text', '') or ''
                sum_req = SummarizerRequest(
                    title=result_state.get('title'),
                    description=content_text[:5000] # Truncate to avoid token overflow
                )
                ai_summary = self.summarizer_service.generate_summary(sum_req)
            except Exception as e:
                logger.warning(f"Summarization failed for article {url}: {e}")

            # Persist Data
            self._persist_results(job, url, result_state, normalized_data, ai_summary)
            
            # Notify User
            title = result_state.get('title') or "Web Article"
            user_phone = payload.get('From', '')
            if user_phone:
                self.notify_user_success(user_phone, title)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}", exc_info=True)
            self._mark_job_failed(job, 'extraction_failed') # Categorize better in real app
            return False

    def _persist_results(self, job: dict, url: str, state: ArticleProcessorState, normalized_data: Optional[Any] = None, ai_summary: Optional[str] = None):
        """Save results to database."""
        job_id = job['id']
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        
        # 1. Update/Insert link_metadata
        existing = self.supabase.table('link_metadata').select('id, scrape_count').eq('url_hash', url_hash).limit(1).execute()
        
        link_id = None
        if existing.data:
            link_id = existing.data[0]['id']
            # Update existing
            update_data = {
                'scrape_count': (existing.data[0].get('scrape_count') or 1) + 1,
                'last_updated_at': 'now()'
            }
            if normalized_data:
                update_data.update({
                    'normalized_category': normalized_data.category.value,
                    'normalized_price_range': normalized_data.price_range.value if normalized_data.price_range else None,
                    'normalized_tags': normalized_data.tags,
                    'ai_summary': ai_summary
                })
            self.supabase.table('link_metadata').update(update_data).eq('id', link_id).execute()
        else:
            # Insert new
            # Prepare metadata JSON
            metadata_json = state.get('metadata') or {}
            if state.get('og_tags'):
                metadata_json['og_tags'] = state['og_tags']
            
            insert_data = {
                'url': url,
                'url_hash': url_hash,
                'platform': state.get('site_name') or 'web',
                'content_type': state.get('content_type') or 'article',
                'extraction_strategy': 'trafilatura', # or 'newspaper' if we tracked it
                'title': state.get('title') or 'Untitled',
                'description': state.get('og_tags', {}).get('description'),
                'author': state.get('author'),
                'summary': state.get('text'), # Storing full text in summary for now (or a real summary if we had one)
                'metadata_json': metadata_json,
                'scrape_status': 'scraped' if not state.get('error') else 'partial',
                'normalized_category': normalized_data.category.value if normalized_data else None,
                'normalized_price_range': normalized_data.price_range.value if normalized_data and normalized_data.price_range else None,
                'normalized_tags': normalized_data.tags if normalized_data else None,
                'ai_summary': ai_summary
            }
            
            # Handle image if available
            if state.get('og_tags') and state['og_tags'].get('og:image'):
                insert_data['thumbnail_url'] = state['og_tags']['og:image']
            elif state.get('metadata') and state['metadata'].get('top_image'):
                insert_data['thumbnail_url'] = state['metadata']['top_image']

            res = self.supabase.table('link_metadata').insert(insert_data).execute()
            if res.data:
                link_id = res.data[0]['id']

        # 2. Insert user_saved_links
        payload = job['payload']
        user_phone = payload.get('From', '').replace('whatsapp:', '')
        
        if link_id and user_phone:
            source_channel_id = job.get('source_channel_id') or user_phone
            source_type = job.get('source_type') or 'dm'
             
            self.supabase.table('user_saved_links').insert({
                'link_id': link_id,
                'user_id': user_phone,
                'source_channel_id': source_channel_id,
                'source_type': source_type,
                'attributed_user_id': user_phone
            }).execute()

        # 3. Update Job
        job_result = {
            'link_id': link_id,
            'title': state.get('title'),
            'content_type': state.get('content_type'),
            'status': 'success'
        }
        self.supabase.table('jobs').update({
            'result': job_result,
            'status': 'complete'
        }).eq('id', job_id).execute()

    def notify_user_success(self, to: str, title: str):
        """Send success notification."""
        try:
            if not to.startswith('whatsapp:'):
                to = f"whatsapp:{to}"
            msg = f"✅ Successfully saved: {title or 'Article'}"
            self.messaging.send_message(to=to, body=msg)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def _mark_job_failed(self, job: dict, error_category: str):
         """Mark job as failed."""
         try:
             self.supabase.table('jobs').update({'status': 'failed'}).eq('id', job['id']).execute()
             # Notify user of failure (optional, can reuse logic from ImageWorker)
         except Exception as e:
             logger.error(f"Failed to mark job failed: {e}")


