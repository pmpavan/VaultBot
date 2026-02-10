#!/usr/bin/env python3
"""Verify YouTube job success."""

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
# Specific job ID from user logs
JOB_ID = "ed35a930-5b72-4f7e-a1a5-1a6848d9f5f3"

print("🔍 Verifying Job Status...")
print("=" * 80)

# Check the job
job = supabase.table('jobs').select('*').eq('id', JOB_ID).execute()

if job.data:
    j = job.data[0]
    print(f"📋 Job Details:")
    print(f"  ID: {j['id']}")
    print(f"  Status: {j['status']}")
    print(f"  Content Type: {j.get('content_type')}")
    print(f"  Platform: {j.get('platform')}")
    print(f"  Result: {j.get('result')}")
    
    if j['status'] == 'complete':
        print("\n✅ Job completed successfully!")
        
        # Check metadata
        links = supabase.table('link_metadata').select('*').order('created_at', desc=True).limit(1).execute()
        if links.data:
            l = links.data[0]
            print(f"\n🔗 Latest Link Metadata:")
            print(f"  URL: {l['url']}")
            print(f"  Title: {l['title']}")
            print(f"  Platform: {l['platform']}")
            print(f"  Created: {l['created_at']}")
        
        # Check saved link
        saved = supabase.table('user_saved_links').select('*').eq('user_id', j['user_phone']).order('saved_at', desc=True).limit(1).execute()
        if saved.data:
            s = saved.data[0]
            print(f"\n👤 Latest Saved Link:")
            print(f"  User: {s['user_id']}")
            print(f"  Link ID: {s['link_id']}")
            print(f"  Saved At: {s['saved_at']}")
            
    elif j['status'] == 'failed':
        print("\n❌ Job failed!")
        print(f"  Error: {j.get('result', {}).get('error', 'Unknown error')}")
else:
    print(f"❌ Job {JOB_ID} not found!")

print("\n" + "=" * 80)
