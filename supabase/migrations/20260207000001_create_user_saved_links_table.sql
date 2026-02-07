-- Create user_saved_links table for user attribution and privacy context
-- This table tracks who saved what link, in which context (DM vs Group)

create table if not exists public.user_saved_links (
  id uuid default gen_random_uuid() primary key,
  
  -- Foreign Keys
  link_id uuid references public.link_metadata(id) on delete cascade,
  user_id text references public.users(phone_number),
  
  -- Privacy Context (from Architecture.md)
  source_channel_id text not null,  -- WhatsApp group ID or DM identifier
  source_type text not null check (source_type in ('dm', 'group')),
  
  -- Attribution (FR-14: Who shared it in group context)
  attributed_user_id text references public.users(phone_number),
  
  -- Metadata
  saved_at timestamptz default now(),
  
  -- Unique constraint: User can't save same link twice in same context
  unique(user_id, link_id, source_channel_id)
);

-- Indexes for common queries
create index idx_user_saved_links_user_id on public.user_saved_links(user_id);
create index idx_user_saved_links_link_id on public.user_saved_links(link_id);
create index idx_user_saved_links_source_channel on public.user_saved_links(source_channel_id);
create index idx_user_saved_links_attributed_user on public.user_saved_links(attributed_user_id);

-- Enable RLS (Row Level Security)
alter table public.user_saved_links enable row level security;

-- Service role: Full access for backend operations
create policy "Service role can manage user_saved_links"
  on public.user_saved_links
  for all
  to service_role
  using (true)
  with check (true);

-- User policy: See own saves + group saves (FR-15: Hybrid Search Scope)
create policy "Users can view their saved links and group links"
  on public.user_saved_links
  for select
  using (
    user_id = current_setting('app.current_user_phone', true)
    or source_channel_id in (
      select source_channel_id 
      from public.user_saved_links 
      where user_id = current_setting('app.current_user_phone', true)
    )
  );

-- Helpful comments
comment on table public.user_saved_links is 'User attribution and privacy context for saved links';
comment on column public.user_saved_links.source_type is 'Message source: dm (direct message) or group';
comment on column public.user_saved_links.attributed_user_id is 'Who shared this link (for group attribution)';
