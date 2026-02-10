-- Add 'api' to extraction_strategy check constraint
-- This is needed for YouTube Data API and other official platform APIs

-- Drop the old constraint
alter table public.link_metadata
  drop constraint link_metadata_extraction_strategy_check;

-- Add new constraint with 'api' included
alter table public.link_metadata
  add constraint link_metadata_extraction_strategy_check
  check (extraction_strategy in ('ytdlp', 'opengraph', 'passthrough', 'vision', 'api'));

-- Update comment
comment on column public.link_metadata.extraction_strategy is 'How metadata was extracted: ytdlp (social), opengraph (generic), passthrough (text), vision (images), api (official platform APIs)';
