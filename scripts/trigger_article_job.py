"""
Script to trigger a manual article extraction job for testing.
Usage: python3 scripts/trigger_article_job.py <url> [phone_number]
"""

import os
import sys
import argparse
import logging
from supabase import create_client

# Add agent/src to path for potential imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../agent/src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_job(url: str, phone: str):
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")
        return

    client = create_client(supabase_url, supabase_key)
    
    payload = {
        'Body': url,
        'From': f"whatsapp:{phone}",
        'To': 'whatsapp:+14155238886' # Sandbox number
    }
    
    data = {
        'type': 'message',
        'source_type': 'whatsapp',
        'source_channel_id': phone,
        'payload': payload,
        'status': 'pending',
        'content_type': 'link' # This targets the ArticleWorker
    }
    
    logger.info(f"Inserting job for URL: {url}...")
    try:
        res = client.table('jobs').insert(data).execute()
        if res.data:
            job_id = res.data[0]['id']
            logger.info(f"✅ Job created successfully! ID: {job_id}")
            logger.info("Make sure 'agent/src/article_worker.py' is running to process this job.")
        else:
            logger.error("Failed to create job (no data returned)")
            
    except Exception as e:
        logger.error(f"Failed to create job: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger an article extraction job")
    parser.add_argument("url", help="URL of the article to extract")
    parser.add_argument("--phone", default="+1234567890", help="User phone number")
    
    args = parser.parse_args()
    trigger_job(args.url, args.phone)
