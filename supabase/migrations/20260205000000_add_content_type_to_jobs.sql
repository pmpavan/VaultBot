-- Migration: Add content_type and platform fields to jobs table
-- Story: 1.3 - Payload Parser & Classification
-- Date: 2026-02-05

-- Add content_type column to jobs table
ALTER TABLE public.jobs
ADD COLUMN IF NOT EXISTS content_type TEXT,
ADD COLUMN IF NOT EXISTS platform TEXT;

-- Add CHECK constraint for content_type ENUM
ALTER TABLE public.jobs
ADD CONSTRAINT jobs_content_type_check 
CHECK (content_type IN ('video', 'image', 'link', 'text'));

-- Add helpful comments
COMMENT ON COLUMN public.jobs.content_type IS 'Type of content: video, image, link, or text';
COMMENT ON COLUMN public.jobs.platform IS 'Platform origin for links: youtube, instagram, tiktok, udemy, coursera, or generic';

-- Create index for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_content_type ON public.jobs(content_type) WHERE content_type IS NOT NULL;
