"""
Classifier Worker - Processes pending jobs and classifies content
Story: 1.3 - Payload Parser & Classification
"""

import os
import sys
from typing import Optional
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nodes.classifier import classify_job_payload


class ClassifierWorker:
    """Worker that processes pending jobs and classifies their content."""
    
    def __init__(self):
        """Initialize Supabase and Twilio clients."""
        self.supabase: Client = create_client(
            os.environ.get('SUPABASE_URL'),
            os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Twilio client for notifications
        self.twilio_client = TwilioClient(
            os.environ.get('TWILIO_ACCOUNT_SID'),
            os.environ.get('TWILIO_AUTH_TOKEN')
        )
        self.twilio_from = os.environ.get('TWILIO_PHONE_NUMBER')
    
    def fetch_and_lock_job(self) -> Optional[dict]:
        """
        Fetch one pending job and atomically update to 'processing'.
        
        Returns:
            Job record if found, None otherwise
        """
        # Atomic pick: SELECT FOR UPDATE SKIP LOCKED pattern
        result = self.supabase.rpc(
            'claim_pending_job',
            {}
        ).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
    
    def classify_and_update(self, job: dict) -> bool:
        """
        Classify job content and update database.
        
        Args:
            job: Job record from database
            
        Returns:
            True if successful, False if failed
        """
        try:
            # Extract payload
            payload = job['payload']
            
            # Classify content
            classification = classify_job_payload(payload)
            
            # Update job with classification
            self.supabase.table('jobs').update({
                'content_type': classification['content_type'],
                'platform': classification['platform'],
                'status': 'pending'  # Ready for next processing node
            }).eq('id', job['id']).execute()
            
            return True
            
        except Exception as e:
            print(f"Classification error for job {job['id']}: {e}")
            
            # Mark as failed
            self.supabase.table('jobs').update({
                'status': 'failed'
            }).eq('id', job['id']).execute()
            
            # Notify user
            self.notify_user_failure(job, str(e))
            
            return False
    
    def notify_user_failure(self, job: dict, error: str):
        """
        Notify user via WhatsApp about processing failure.
        
        Args:
            job: Job record
            error: Error message
        """
        try:
            payload = job['payload']
            user_phone = payload.get('From', '')
            
            if user_phone:
                self.twilio_client.messages.create(
                    from_=self.twilio_from,
                    to=user_phone,
                    body=f"⚠️ Couldn't process your message. Error: {error[:100]}"
                )
        except Exception as e:
            print(f"Failed to send notification: {e}")
    
    def process_one_job(self) -> bool:
        """
        Process one job from the queue.
        
        Returns:
            True if a job was processed, False if queue is empty
        """
        job = self.fetch_and_lock_job()
        
        if not job:
            return False
        
        self.classify_and_update(job)
        return True
    
    def run_loop(self, max_iterations: Optional[int] = None):
        """
        Run worker loop to process jobs.
        
        Args:
            max_iterations: Maximum number of iterations (None for infinite)
        """
        iteration = 0
        
        while True:
            if max_iterations and iteration >= max_iterations:
                break
            
            processed = self.process_one_job()
            
            if not processed:
                # No jobs available, wait before retrying
                import time
                time.sleep(5)
            
            iteration += 1


if __name__ == '__main__':
    worker = ClassifierWorker()
    worker.run_loop()
