
-- Create jobs table for ingestion pipeline
-- This table stores webhook events from Twilio for async processing
create table if not exists public.jobs (
  id uuid default gen_random_uuid() primary key,
  user_id text references public.users(phone_number),  -- Phone-based FK (not auth.users)
  source_channel_id text not null,  -- WhatsApp group ID or DM identifier
  source_type text not null check (source_type in ('dm', 'group')),  -- ENUM constraint
  user_phone text not null,  -- Denormalized for quick access
  payload jsonb not null,  -- Full webhook payload from Twilio
  status text default 'pending' check (status in ('pending', 'processing', 'complete', 'failed')),  -- ENUM constraint
  created_at timestamptz default now()
);

-- Enable RLS (Row Level Security)
alter table public.jobs enable row level security;

-- Service role policies: Full access for backend operations
drop policy if exists "Service role can manage jobs" on public.jobs;
create policy "Service role can manage jobs"
  on public.jobs
  for all
  to service_role
  using (true)
  with check (true);

-- Create indexes for common queries
create index if not exists idx_jobs_status on public.jobs(status) where status = 'pending';
create index if not exists idx_jobs_user_id on public.jobs(user_id);
create index if not exists idx_jobs_created_at on public.jobs(created_at);

-- Add helpful comments
comment on table public.jobs is 'Job queue for async processing of WhatsApp webhook events';
comment on column public.jobs.user_id is 'References users.phone_number (phone-based identity)';
comment on column public.jobs.source_type is 'Message source: dm (direct message) or group';
comment on column public.jobs.status is 'Processing status: pending, processing, complete, or failed';
