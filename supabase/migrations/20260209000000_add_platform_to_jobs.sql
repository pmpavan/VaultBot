-- Add platform column to jobs table for routing between workers
-- Story: 2.5 - Text Article Parser
-- Date: 2026-02-09

-- Add platform column (nullable for backward compatibility)
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS platform TEXT;

-- Add index for worker queries
CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform);

-- Add comment
COMMENT ON COLUMN jobs.platform IS 'Platform identifier for routing: youtube, instagram, tiktok, generic, etc. Used by workers to filter jobs.';
