#!/usr/bin/env python3
"""Debug script to check YouTube link processing flow."""

import os
import sys
from supabase import create_client

# Load environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 80)
print("🔍 DEBUGGING YOUTUBE LINK PROCESSING")
print("=" * 80)

# Check recent jobs
print("\n📋 Recent Jobs (last 10):")
print("-" * 80)
jobs = supabase.table('jobs').select('id, content_type, platform, status, created_at, user_phone, result').order('created_at', desc=True).limit(10).execute()
if jobs.data:
    for job in jobs.data:
        platform = job.get('platform') or 'NULL'
        result = job.get('result', {})
        error = result.get('error', '') if isinstance(result, dict) else ''
        print(f"  {job['created_at'][:19]} | {job['content_type']:10} | {platform:10} | {job['status']:10} | {job['user_phone']}")
        if error:
            print(f"    ❌ Error: {error[:100]}")
else:
    print("  ❌ No jobs found!")

# Check jobs by status
print("\n📊 Jobs by Status:")
print("-" * 80)
statuses = supabase.table('jobs').select('status, content_type, platform').execute()
if statuses.data:
    from collections import Counter
    status_counts = Counter((j['status'], j.get('content_type', 'NULL'), j.get('platform', 'NULL')) for j in statuses.data)
    for (status, content_type, platform), count in status_counts.most_common():
        print(f"  {status:10} | {content_type:10} | {platform:10} | Count: {count}")
else:
    print("  ❌ No jobs found!")

# Check DLQ
print("\n💀 Dead Letter Queue (last 5):")
print("-" * 80)
dlq = supabase.table('dlq_jobs').select('*').order('created_at', desc=True).limit(5).execute()
if dlq.data:
    for entry in dlq.data:
        print(f"  {entry['created_at'][:19]} | {entry['error_type']:20} | {entry['error_message'][:60]}")
else:
    print("  ✅ No DLQ entries (good!)")

# Check link_metadata
print("\n🔗 Link Metadata (last 5):")
print("-" * 80)
links = supabase.table('link_metadata').select('id, url, content_type, created_at').order('created_at', desc=True).limit(5).execute()
if links.data:
    for link in links.data:
        print(f"  {link['created_at'][:19]} | {link['content_type']:10} | {link['url'][:60]}")
else:
    print("  ❌ No link metadata found!")

# Check user_saved_links
print("\n👤 User Saved Links (last 5):")
print("-" * 80)
saved = supabase.table('user_saved_links').select('*').order('saved_at', desc=True).limit(5).execute()
if saved.data:
    for s in saved.data:
        print(f"  {s['saved_at'][:19]} | User: {s['user_id']} | Link: {s['link_id']}")
else:
    print("  ❌ No saved links found!")

# Check for pending YouTube jobs specifically
print("\n🎥 Pending YouTube Jobs:")
print("-" * 80)
youtube_jobs = supabase.table('jobs').select('*').eq('content_type', 'link').eq('platform', 'youtube').eq('status', 'pending').execute()
if youtube_jobs.data:
    print(f"  Found {len(youtube_jobs.data)} pending YouTube jobs:")
    for job in youtube_jobs.data:
        print(f"    ID: {job['id']}")
        print(f"    Created: {job['created_at']}")
        print(f"    Payload: {job.get('payload', {}).get('Body', 'N/A')}")
else:
    print("  ✅ No pending YouTube jobs")

print("\n" + "=" * 80)
print("✅ Debug check complete")
print("=" * 80)
