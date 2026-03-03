-- Enable pg_net extension for HTTP requests
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Table to store worker service URLs
CREATE TABLE IF NOT EXISTS public.worker_config (
    worker_name TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    secret TEXT, -- Optional override for WORKER_SECRET
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Insert placeholders (User needs to replace these after deployment)
INSERT INTO public.worker_config (worker_name, url) VALUES
('classifier', 'https://vaultbot-classifier-service-ixdoczhvuvqpqzcjgrcj-uc.a.run.app/process'),
('scraper', 'https://vaultbot-scraper-service-ixdoczhvuvqpqzcjgrcj-uc.a.run.app/process'),
('video', 'https://vaultbot-video-service-ixdoczhvuvqpqzcjgrcj-uc.a.run.app/process'),
('image', 'https://vaultbot-image-service-ixdoczhvuvqpqzcjgrcj-uc.a.run.app/process'),
('article', 'https://vaultbot-article-service-ixdoczhvuvqpqzcjgrcj-uc.a.run.app/process')
ON CONFLICT (worker_name) DO NOTHING;

-- Trigger logic for routing jobs
CREATE OR REPLACE FUNCTION public.on_job_created()
RETURNS TRIGGER AS $$
DECLARE
    target_worker TEXT;
    target_url TEXT;
    worker_secret TEXT;
BEGIN
    -- Determine worker based on content_type or status
    -- Classifier handles EVERYTHING that comes in as 'pending' with no content_type
    IF NEW.content_type IS NULL OR NEW.content_type = '' THEN
        target_worker := 'classifier';
    ELSIF NEW.content_type = 'link' AND (NEW.platform IS NULL OR NEW.platform != 'generic') THEN
        target_worker := 'scraper';
    ELSIF NEW.content_type = 'link' AND NEW.platform = 'generic' THEN
        target_worker := 'article';
    ELSIF NEW.content_type = 'image' THEN
        target_worker := 'image';
    ELSIF NEW.content_type = 'video' THEN
        target_worker := 'video';
    ELSE
        RETURN NEW; -- Ignore unknown types
    END IF;

    -- Get URL and Secret from config
    SELECT url INTO target_url FROM public.worker_config WHERE worker_name = target_worker;
    
    -- Fallback to default secret if not specific to worker
    -- We assume the secret is managed via vault or provided as an environment variable
    -- In Supabase, we can use net.http_post to send the request
    IF target_url IS NOT NULL THEN
        PERFORM net.http_post(
            url := target_url,
            headers := jsonb_build_object(
                'Content-Type', 'application/json',
                'X-VaultBot-Worker-Secret', current_setting('vaultbot.worker_secret', true) -- Using GUC for secret
            ),
            body := jsonb_build_object('job_id', NEW.id)
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create the trigger
DROP TRIGGER IF EXISTS tr_on_job_created ON public.jobs;
CREATE TRIGGER tr_on_job_created
    AFTER INSERT ON public.jobs
    FOR EACH ROW
    WHEN (NEW.status = 'pending')
    EXECUTE FUNCTION public.on_job_created();
