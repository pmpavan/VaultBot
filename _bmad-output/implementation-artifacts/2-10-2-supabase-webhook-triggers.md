# Story 2.10.2: Supabase Webhook Triggers

## Description
This story implements the event-driven trigger mechanism for VaultBot's worker fleet. By leveraging Supabase Database Webhooks, we eliminate the need for workers to poll the `jobs` table. Instead, a webhook is fired immediately upon job creation, triggering the appropriate Cloud Run worker via an HTTP POST request. This enables a true scale-to-zero architecture where workers only consume resources when active tasks exist.

## Requirements
- **Event-Driven Execution**: Trigger workers via webhooks on `INSERT` events to the `public.jobs` table.
- **Routing Logic**: Implement a SQL trigger function that routes jobs based on their `content_type` (e.g., `link` -> Scraper, `video` -> Video Worker).
- **Scale-to-Zero Compatibility**: Migrate all workers from Cloud Run Jobs to Cloud Run Services to support HTTP-based activation.
- **Security**: Implement a shared secret (`WORKER_SECRET`) passed in an `X-VaultBot-Worker-Secret` header to authenticate Supabase requests.

## Acceptance Criteria
- [x] All workers (Classifier, Scraper, Video, Image, Article) are deployed as Cloud Run Services.
- [x] Supabase `pg_net` extension is enabled and configured.
- [x] A SQL trigger `on_job_created` is active on the `jobs` table.
- [x] Webhook requests include the `X-VaultBot-Worker-Secret` header.
- [x] Workers validate the `X-VaultBot-Worker-Secret` before processing.
- [x] End-to-end flow: Sending a WhatsApp link triggers the classifier, which updates content type, which triggers the specific worker, all via webhooks.

## Tasks
- [x] **Infrastructure**: Create `agent/deploy-services.sh` to deploy workers as Cloud Run Services.
- [x] **Security**: Generate a secure `WORKER_SECRET` and configure it in Supabase and Cloud Run.
- [x] **Database**: Create and apply SQL migration for database webhooks and trigger routing logic.
- [x] **Worker Logic**: Update FastAPI apps to validate the security header and respond correctly to webhooks.
- [x] **Verification**: Manually test the full event-driven chain from message ingestion to final processing.

## Dev Notes
- **pg_net**: Use the `supabase_functions.http_request` or the built-in Webhook UI (if scripted via SQL).
- **Concurrency**: Cloud Run Services should be configured with `max-concurrency` and `max-instances` to manage load.
- **Retry Mechanism**: Supabase webhooks have a configurable timeout; ensure workers respond with 202 or 200 quickly.

## Status
Status: review

## Dev Agent Record
- **Implementation Plan**: Approved and followed.
- **Verification**: Verified security header validation with automated tests (`agent/tests/test_webhook_security.py`).
- **Files Created**: `agent/deploy-services.sh`, `agent/supabase/configure-webhooks.sql`.
- **References**: Epic 2.10, Story 2.10.1.
