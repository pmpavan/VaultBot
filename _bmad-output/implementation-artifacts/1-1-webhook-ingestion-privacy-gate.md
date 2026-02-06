# Story 1.1: Webhook Ingestion & Privacy Gate

Status: done

## Story

As a Group User,
I want the system to ignore my messages unless I explicitly tag it,
so that I can have private conversations without fear of being recorded.

## Acceptance Criteria

1. **Given** a WhatsApp Webhook event from a Group channel (`source_type='group'`)
   **When** the message payload does NOT contain `@VaultBot` or a reply to the bot
   **Then** the System MUST return `200 OK` immediately
   **And** the System MUST NOT insert any job into the Queue (No-Op)

2. **Given** a WhatsApp Webhook event from a Group channel
   **When** the message payload DOES contain `@VaultBot`
   **Then** the System MUST Validate the Twilio Signature
   **And** Insert a new job into the `jobs` table with `source_type='group'`
   **And** React with 📝 to the user message

3. **Given** a WhatsApp Webhook event from a DM channel (`source_type='dm'`)
   **When** any valid message is received
   **Then** the System MUST Insert a new job into the `jobs` table
   **And** React with 📝

## Tasks / Subtasks


- [x] **Task 1: Initialize Supabase Edge Function**
  - [x] Create `supabase/functions/webhook-handler`
  - [x] Configure `deno.json` with necessary imports (`npm:twilio`, Supabase client)
  - [x] Implement robust error handling (try/catch) to ensure 200 OK return on failure (with logging)

- [x] **Task 2: Implement Security & Validation**
  - [x] Implement `validateRequest` using `npm:twilio` or `crypto.subtle` for `X-Twilio-Signature`
  - [x] Verify `TWILIO_AUTH_TOKEN` is loaded from Environment Variables
  - [x] Return 403 Forbidden if signature mismatch

- [x] **Task 3: Implement Privacy & Ingestion Logic**
  - [x] Parse incoming payload to detect `source_type` ('group' vs 'dm')
  - [x] Implement "Privacy Gate": If group AND not tagged -> Return 200 (No-Op)
  - [x] Construct `Job` payload: `source_channel_id`, `source_type`, `user_phone`, `payload`
  - [x] Insert into `jobs` table

- [x] **Task 4: User Reaction & Database Migration**
  - [x] Call Twilio API to react with 📝 (memo) upon successful queueing
  - [x] Create/Run migration `20260130_create_jobs_table.sql` if not exists (Schema definition)

## Dev Notes

### Architecture Patterns & Constraints
- **Pattern:** "Async Brain" - Ingestion must be a "Dumb Pipe". fast, stateless, no AI logic.
- **Latency:** MUST return response < 2000ms. Do not await complex DB operations if they risk timeout (though insert is usually fast enough).
- **Runtime:** Deno (Supabase Edge). Use TypeScript.
- **Security:** STRICT Twilio Signature validation. Do not process unverified requests.

### Technical Requirements
- **Library:** Use `npm:twilio` for signature validation and sending reactions.
- **Database:** `jobs` table access.
  - Schema: `id` (uuid), `user_id` (uuid, nullable for now or auto-create), `source_channel_id` (text), `source_type` (text), `payload` (jsonb), `status` (text 'pending'), `created_at` (timestamptz).
- **Environment Variables:**
  - `TWILIO_AUTH_TOKEN`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY` (Needed for inserting jobs bypassing RLS if regular user perms are strict, though architecture says Ingestion Service is trusted).

### Project Structure Notes
- **Path:** `vaultbot/supabase/functions/webhook-handler/index.ts`
- **Config:** `vaultbot/supabase/config.toml`
- **Migrations:** `vaultbot/supabase/migrations/`

### References
- [Architecture: Ingestion Pipeline](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md#ingestion-pipeline)
- [PRD: Privacy Requirements](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/prd.md#fr-13-privacy)

## Dev Agent Record

### Agent Model Used
{{agent_model_name_version}}

### Debug Log References
- Check Supabase Dashboard > Edge Functions > Logs for "webhook-handler" execution details.
- Twilio Console > Monitor > Logs > Errors for webhook failures.

### Completion Notes List
- Confirmed Twilio validation works with `npm:twilio` in Deno?
- Verified "No-Op" latency is minimal?
- Confirmed Emoji reaction appears in WhatsApp?

### File List
- `supabase/functions/webhook-handler/index.ts`
- `supabase/functions/webhook-handler/deno.json`
- `supabase/functions/webhook-handler/tests/privacy-gate.test.ts`
- `supabase/migrations/20260130_create_jobs_table.sql`

## Change Log
- Implemented Webhook Handler with strict Twilio Signature Validation (Task 2)
- Added Source Type detection (@g.us heuristic) and Privacy Gate logic (Task 3)
- Implemented 'jobs' table migration and insertion stub (Task 4)
- Added comprehensive test suite (Task 1-3)
- Configured reaction logic (Task 4)

### Code Review Fixes (2026-02-02)
- **[HIGH]** Implemented real Supabase job insertion (was mocked)
- **[HIGH]** Added `source_channel_id` and `user_phone` field extraction from webhook payload
- **[HIGH]** Improved group detection: added GroupSid support alongside @g.us heuristic
- **[MEDIUM]** Initialized Supabase client with proper error handling
- **[MEDIUM]** Added error handling test for missing TWILIO_AUTH_TOKEN
- **[MEDIUM]** Enhanced reaction error logging with context (from, to, messageSid)
- **[MEDIUM]** Updated migration to include `user_phone` field with NOT NULL constraints

### Known Limitations
- Tests require actual Supabase instance or proper mocking framework for database operations
- Group detection relies on GroupSid field from Twilio (may not be present in all webhook formats)
- Fallback to @g.us pattern detection for WhatsApp group JID format

