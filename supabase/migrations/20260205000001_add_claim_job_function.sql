-- Migration: Add atomic job claiming function
-- Story: 1.3 - Payload Parser & Classification
-- Date: 2026-02-05

-- Function to atomically claim a pending job
CREATE OR REPLACE FUNCTION claim_pending_job()
RETURNS SETOF jobs
LANGUAGE plpgsql
AS $$
DECLARE
    claimed_job jobs;
BEGIN
    -- Select and lock one pending job, skip locked rows
    SELECT * INTO claimed_job
    FROM jobs
    WHERE status = 'pending'
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;
    
    -- If found, update to processing
    IF FOUND THEN
        UPDATE jobs
        SET status = 'processing'
        WHERE id = claimed_job.id;
        
        RETURN QUERY SELECT * FROM jobs WHERE id = claimed_job.id;
    END IF;
    
    RETURN;
END;
$$;

-- Grant execute permission to service role
GRANT EXECUTE ON FUNCTION claim_pending_job() TO service_role;

COMMENT ON FUNCTION claim_pending_job() IS 'Atomically claims one pending job and marks it as processing';
