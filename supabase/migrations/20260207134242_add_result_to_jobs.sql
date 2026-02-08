-- Migration: Add result field to jobs table for storing processing results
-- Story: 2.3 - Video Frame Extraction
-- Date: 2026-02-07

-- Add result column to jobs table
ALTER TABLE public.jobs
ADD COLUMN IF NOT EXISTS result JSONB;

-- Add helpful comment
COMMENT ON COLUMN public.jobs.result IS 'Processing results (e.g., video summary, extracted data, link metadata)';

-- Create index for querying results
CREATE INDEX IF NOT EXISTS idx_jobs_result ON public.jobs USING GIN (result) WHERE result IS NOT NULL;
