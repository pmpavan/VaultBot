-- Create link_metadata table for deduplicated, publicly available link data
-- This table stores extracted metadata for each unique URL, regardless of who saved it

create table if not exists public.link_metadata (
  id uuid default gen_random_uuid() primary key,
  url text unique not null,  -- Canonical URL (normalized)
  url_hash text unique not null,  -- SHA-256 hash for fast lookups
  
  -- Platform Detection
  platform text not null,  -- 'instagram', 'tiktok', 'youtube', 'blog', 'news', 'generic'
  content_type text not null check (content_type in ('video', 'image', 'article', 'link')),
  extraction_strategy text not null check (extraction_strategy in ('ytdlp', 'opengraph', 'passthrough', 'vision')),
  
  -- Extracted Metadata
  title text,
  description text,
  author text,
  thumbnail_url text,
  duration integer,  -- seconds, for videos
  publish_date timestamptz,
  
  -- Full Content (for articles/blogs - Story 2.5)
  full_text text,
  
  -- AI-Generated Fields (from Epic 2 stories)
  ai_summary text,  -- Story 2.7: Natural Language Summary
  normalized_category text,  -- Story 2.6: Data Normalizer
  normalized_price_range text,  -- Story 2.6
  normalized_tags jsonb,  -- Story 2.6: Array of tags
  
  -- Vector Embedding (Epic 3)
  embedding vector(1536),  -- OpenAI text-embedding-3-small
  
  -- Metadata
  scrape_status text default 'pending' check (scrape_status in ('pending', 'scraped', 'failed', 'partial')),
  scrape_error text,  -- Error message if scraping failed
  first_scraped_at timestamptz default now(),
  last_updated_at timestamptz default now(),
  scrape_count integer default 1  -- How many times this URL was requested
);

-- Indexes for common queries
create index idx_link_metadata_url_hash on public.link_metadata(url_hash);
create index idx_link_metadata_platform on public.link_metadata(platform);
create index idx_link_metadata_content_type on public.link_metadata(content_type);
create index idx_link_metadata_scrape_status on public.link_metadata(scrape_status) where scrape_status = 'pending';

-- Vector index for semantic search (Epic 3)
create index idx_link_metadata_embedding on public.link_metadata using hnsw (embedding vector_cosine_ops);

-- Helpful comments
comment on table public.link_metadata is 'Deduplicated link metadata - one row per unique URL';
comment on column public.link_metadata.url_hash is 'SHA-256 hash of URL for fast deduplication checks';
comment on column public.link_metadata.scrape_count is 'Number of times this URL has been saved by users';
comment on column public.link_metadata.extraction_strategy is 'How metadata was extracted: ytdlp (social), opengraph (generic), passthrough (text), vision (images)';
