-- Enable RLS (Row Level Security)
alter table public.link_metadata enable row level security;

-- Service role policies: Full access for backend operations
drop policy if exists "Service role can manage link_metadata" on public.link_metadata;
create policy "Service role can manage link_metadata"
  on public.link_metadata
  for all
  to service_role
  using (true)
  with check (true);

-- Authenticated users policies: Read access to metadata
drop policy if exists "Authenticated users can read link_metadata" on public.link_metadata;
create policy "Authenticated users can read link_metadata"
  on public.link_metadata
  for select
  to authenticated
  using (true);
