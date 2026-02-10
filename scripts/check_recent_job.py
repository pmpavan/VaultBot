#!/usr/bin/env python3
"""Check the most recent job created for a YouTube URL."""

import os
import sys
from supabase import create_client

# Load environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("🔍 Checking most recent job...")
print("=" * 80)

# Get the most recent job
job = supabase.table('jobs').select('*').order('created_at', desc=True).limit(1).execute()

if job.data:
    j = job.data[0]
    print(f"📋 Most Recent Job:")
    print(f"  ID: {j['id']}")
    print(f"  Created: {j['created_at']}")
    print(f"  Status: {j['status']}")
    print(f"  Content Type: {j.get('content_type', 'NULL')}")
    print(f"  Platform: {j.get('platform', 'NULL')}")
    print(f"  User Phone: {j['user_phone']}")
    print(f"  Payload Body: {j.get('payload', {}).get('Body', 'N/A')}")
    print(f"  Result: {j.get('result')}")
    print()
    
    # Check which worker should pick this up
    content_type = j.get('content_type')
    platform = j.get('platform')
    
    print("🤖 Worker Routing Analysis:")
    print("-" * 80)
    
    if not content_type:
        print("  ❌ ISSUE: content_type is NULL!")
        print("  → Classifier worker should have set this")
        print("  → Check if classifier worker is running")
    elif content_type == 'link':
        if platform == 'youtube':
            print("  ✅ Should be picked up by: SCRAPER WORKER")
            print("  → Query: content_type='link' AND platform='youtube'")
        elif platform == 'generic':
            print("  ✅ Should be picked up by: ARTICLE WORKER")
            print("  → Query: content_type='link' AND platform='generic'")
        else:
            print(f"  ⚠️  Platform: {platform}")
            print("  → Check worker queries")
    elif content_type == 'video':
        print("  ✅ Should be picked up by: VIDEO WORKER")
    elif content_type == 'image':
        print("  ✅ Should be picked up by: IMAGE WORKER")
    else:
        print(f"  ⚠️  Unknown content_type: {content_type}")
    
    print()
    print("📊 Job Counts by Status:")
    print("-" * 80)
    
    # Count jobs by status for this content_type/platform combo
    if content_type and platform:
        jobs = supabase.table('jobs').select('status').eq('content_type', content_type).eq('platform', platform).execute()
        if jobs.data:
            from collections import Counter
            status_counts = Counter(j['status'] for j in jobs.data)
            for status, count in status_counts.most_common():
                print(f"  {status}: {count}")
    
else:
    print("❌ No jobs found!")

print()
print("=" * 80)
