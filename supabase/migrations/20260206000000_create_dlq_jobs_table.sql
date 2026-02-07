-- Migration: Create Dead Letter Queue (DLQ) table
-- Story: 1.5 - Dead Letter Queue
-- Purpose: Capture failed webhook processing attempts for debugging and analysis

-- Create dlq_jobs table
CREATE TABLE IF NOT EXISTS dlq_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_payload JSONB NOT NULL,
  error_message TEXT NOT NULL,
  error_type TEXT NOT NULL,
  user_phone TEXT,
  source_type TEXT,
  source_channel_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE dlq_jobs ENABLE ROW LEVEL SECURITY;

-- Service role has full access to DLQ (for admin/monitoring)
CREATE POLICY "Service role has full access to DLQ"
  ON dlq_jobs
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Create index for querying by timestamp (most recent errors first)
CREATE INDEX idx_dlq_jobs_created_at ON dlq_jobs(created_at DESC);

-- Create index for querying by error type (for categorization)
CREATE INDEX idx_dlq_jobs_error_type ON dlq_jobs(error_type);

-- Create index for querying by user phone (for user-specific debugging)
CREATE INDEX idx_dlq_jobs_user_phone ON dlq_jobs(user_phone) WHERE user_phone IS NOT NULL;

-- Add comment for documentation
COMMENT ON TABLE dlq_jobs IS 'Dead Letter Queue for failed webhook processing attempts. Stores original payload and error context for debugging.';
COMMENT ON COLUMN dlq_jobs.original_payload IS 'Complete webhook payload that failed processing (JSONB for queryability)';
COMMENT ON COLUMN dlq_jobs.error_message IS 'Error message from the exception';
COMMENT ON COLUMN dlq_jobs.error_type IS 'Error type/name (e.g., DatabaseError, ValidationError)';
COMMENT ON COLUMN dlq_jobs.user_phone IS 'Phone number extracted from payload (if available) for easier debugging';
COMMENT ON COLUMN dlq_jobs.source_type IS 'Source type (dm/group) extracted from context (if available)';
COMMENT ON COLUMN dlq_jobs.source_channel_id IS 'Channel ID extracted from context (if available)';
