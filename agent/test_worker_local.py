"""
Local Testing Script for Classifier Worker
Story: 1.3 - Payload Parser & Classification

This script helps you test the classifier locally by:
1. Creating a test job in the database
2. Running the worker to process it
3. Verifying the classification results
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env.local (for local testing)
# Falls back to .env if .env.local doesn't exist
load_dotenv('.env.local')
if not os.environ.get('SUPABASE_URL'):
    load_dotenv()  # Fallback to .env

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nodes.classifier import classify_job_payload


def get_supabase_client():
    """Get Supabase client (lazy initialization)."""
    from supabase import create_client
    return create_client(
        os.environ.get('SUPABASE_URL'),
        os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    )


def create_test_job(payload_type='youtube'):
    """Create a test job in the database."""
    
    supabase = get_supabase_client()
    
    test_phone = '+1234567890'
    
    # Ensure test user exists
    try:
        supabase.table('users').insert({
            'phone_number': test_phone,
            'first_name': 'Test User'
        }).execute()
        print(f"✅ Created test user: {test_phone}")
    except Exception as e:
        # User might already exist, that's fine
        print(f"ℹ️  Test user already exists: {test_phone}")
    
    test_payloads = {
        'youtube': {
            'NumMedia': '0',
            'Body': 'Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'From': test_phone,
            'source_type': 'dm'
        },
        'instagram': {
            'NumMedia': '0',
            'Body': 'Amazing reel: https://www.instagram.com/reel/ABC123xyz/',
            'From': test_phone,
            'source_type': 'dm'
        },
        'image': {
            'NumMedia': '1',
            'MediaContentType0': 'image/jpeg',
            'Body': '',
            'From': test_phone,
            'source_type': 'dm'
        },
        'video': {
            'NumMedia': '1',
            'MediaContentType0': 'video/mp4',
            'Body': '',
            'From': test_phone,
            'source_type': 'dm'
        },
        'text': {
            'NumMedia': '0',
            'Body': 'Just a regular text message',
            'From': test_phone,
            'source_type': 'dm'
        }
    }
    
    payload = test_payloads.get(payload_type, test_payloads['youtube'])
    
    # Insert test job with correct schema
    result = supabase.table('jobs').insert({
        'user_id': test_phone,  # FK to users.phone_number
        'source_channel_id': 'test-channel-123',
        'source_type': payload.get('source_type', 'dm'),
        'user_phone': test_phone,  # Denormalized for quick access
        'payload': payload,
        'status': 'pending'
    }).execute()
    
    job_id = result.data[0]['id']
    print(f"✅ Created test job: {job_id}")
    print(f"   Type: {payload_type}")
    print(f"   Payload: {payload.get('Body', 'Media attachment')[:50]}...")
    
    return job_id


def test_classification_only(payload_type='youtube'):
    """Test classification logic without database."""
    
    test_payloads = {
        'youtube': {
            'NumMedia': '0',
            'Body': 'Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        },
        'instagram': {
            'NumMedia': '0',
            'Body': 'https://www.instagram.com/reel/ABC123xyz/'
        },
        'udemy': {
            'NumMedia': '0',
            'Body': 'Great course: https://www.udemy.com/course/python-bootcamp/'
        },
        'coursera': {
            'NumMedia': '0',
            'Body': 'https://www.coursera.org/learn/machine-learning'
        },
        'image': {
            'NumMedia': '1',
            'MediaContentType0': 'image/jpeg',
            'Body': ''
        },
        'video': {
            'NumMedia': '1',
            'MediaContentType0': 'video/mp4',
            'Body': ''
        }
    }
    
    payload = test_payloads.get(payload_type, test_payloads['youtube'])
    
    print(f"\n🧪 Testing classification for: {payload_type}")
    print(f"   Payload: {payload}")
    
    result = classify_job_payload(payload)
    
    print(f"\n✅ Classification Result:")
    print(f"   Content Type: {result['content_type']}")
    print(f"   Platform: {result['platform']}")
    
    return result


def run_worker_once():
    """Run the worker to process one job."""
    from worker import ClassifierWorker
    
    print("\n🤖 Starting worker (processing 1 job)...")
    
    worker = ClassifierWorker()
    processed = worker.process_one_job()
    
    if processed:
        print("✅ Job processed successfully!")
    else:
        print("ℹ️  No pending jobs found")
    
    return processed


def verify_job_classification(job_id):
    """Verify that a job was classified correctly."""
    
    supabase = get_supabase_client()
    
    result = supabase.table('jobs').select('*').eq('id', job_id).execute()
    
    if result.data:
        job = result.data[0]
        print(f"\n📊 Job {job_id} Status:")
        print(f"   Status: {job['status']}")
        print(f"   Content Type: {job.get('content_type', 'NOT SET')}")
        print(f"   Platform: {job.get('platform', 'NOT SET')}")
        
        return job
    else:
        print(f"❌ Job {job_id} not found")
        return None


def main():
    """Main test flow."""
    
    print("=" * 60)
    print("VaultBot Classifier Worker - Local Testing")
    print("=" * 60)
    
    # Test 1: Classification logic only (no database)
    print("\n📋 TEST 1: Classification Logic (No Database)")
    print("-" * 60)
    
    for payload_type in ['youtube', 'instagram', 'udemy', 'image', 'video']:
        test_classification_only(payload_type)
    
    # Test 2: End-to-end with database
    print("\n\n📋 TEST 2: End-to-End with Database")
    print("-" * 60)
    
    # Create test job
    job_id = create_test_job('youtube')
    
    # Run worker
    run_worker_once()
    
    # Verify results
    verify_job_classification(job_id)
    
    print("\n" + "=" * 60)
    print("✅ Testing Complete!")
    print("=" * 60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test the classifier worker')
    parser.add_argument('--mode', choices=['logic', 'e2e', 'full'], default='full',
                        help='Test mode: logic (classification only), e2e (end-to-end), full (both)')
    parser.add_argument('--type', choices=['youtube', 'instagram', 'udemy', 'coursera', 'image', 'video', 'text'],
                        default='youtube', help='Payload type to test')
    
    args = parser.parse_args()
    
    if args.mode == 'logic':
        test_classification_only(args.type)
    elif args.mode == 'e2e':
        job_id = create_test_job(args.type)
        run_worker_once()
        verify_job_classification(job_id)
    else:
        main()
