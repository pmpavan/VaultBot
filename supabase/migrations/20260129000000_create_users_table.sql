
-- Create users table for phone-based identity
-- VaultBot uses phone numbers as primary identifiers (no auth.users for MVP)
create table if not exists public.users (
  phone_number text primary key,  -- Format: +1234567890 (E.164 format)
  first_name text,
  created_at timestamptz default now()
);

-- Enable RLS (Row Level Security)
alter table public.users enable row level security;

-- Service role policies: Full access for backend operations
create policy "Service role can manage users"
  on public.users
  for all
  to service_role
  using (true)
  with check (true);

-- Create index for faster lookups (optional but recommended)
create index if not exists idx_users_created_at on public.users(created_at);

-- Add helpful comment
comment on table public.users is 'User profiles identified by phone number (WhatsApp-based identity)';
comment on column public.users.phone_number is 'E.164 format phone number (e.g., +15551234567)';
