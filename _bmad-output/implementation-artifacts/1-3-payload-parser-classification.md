# Story 1.3: Payload Parser & Classification

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a System,
I want to classify incoming content as Link, Image, or Video,
so that the correct downstream agent can process it.

## Acceptance Criteria

1. **Given** a 'pending' job in the queue
2. **When** the Processor Node picks it up
3. **Then** it MUST parse the JSON payload to detect content type
4. **And** Identify the Platform (Instagram, TikTok, YouTube, Udemy, Coursera, Generic) if it is a Link
5. **And** Update the job `content_type` field with the result ('video', 'image', 'link', 'text')
6. **And** If content is unsupported, mark job as 'failed' and notify user

## Tasks / Subtasks

- [x] **Task 1: Database Schema Expansion** (AC: 5)
  - [x] Create migration `20260205000000_add_content_type_to_jobs.sql`
  - [x] Add `content_type` column to `jobs` table (TEXT, nullable initially)
  - [x] Add CHECK constraint for `content_type` IN ('video', 'image', 'link', 'text')
  - [x] Add `platform` column for link platform identification
  - [x] Create atomic job claiming function `claim_pending_job()`

- [x] **Task 2: Implement Classification Heuristics** (AC: 3, 4)
  - [x] Implement `detectContentType` logic:
    - [x] Check `NumMedia`. If `> 0`, use `MediaContentType0` to distinguish 'image' vs 'video'.
    - [x] If `NumMedia == 0`, search `Body` for URLs.
    - [x] If URL found, classify as 'link'.
    - [x] If no URL and no media, classify as 'text'.
  - [x] Implement `identifyPlatform` logic for Links:
    - [x] Regex for YouTube: `/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/i`
    - [x] Regex for Instagram: `/instagram\.com\/(?:p|reels|reel)\/([a-zA-Z0-9_-]+)/i`
    - [x] Regex for TikTok: `/tiktok\.com\/(?:@[\w.-]+\/video\/|v\/|t\/|[\w.-]+\/|)([\w.-]+)/i`
    - [x] Regex for Udemy: `/udemy\.com\/course\/([a-zA-Z0-9_-]+)/i`
    - [x] Regex for Coursera: `/coursera\.org\/(?:learn|specializations|professional-certificates)\/([a-zA-Z0-9_-]+)/i`
    - [x] Default to 'Generic' if no match.

- [x] **Task 3: Implement Processor Worker** (AC: 1, 2, 5, 6)
  - [x] Initialize `agent/` directory:
    - [x] Create `agent/src/nodes/classifier.py`
    - [x] Create `agent/requirements.txt`
  - [x] Implement a worker loop that:
    - [x] Fetches ONE job with `status = 'pending'` and updates it to `status = 'processing'` (atomic pick).
    - [x] Runs classification logic.
    - [x] Updates job with `content_type`, `platform`, and sets `status = 'pending'` (ready for next agent node) or `status = 'failed'` (if error).
    - [x] If 'failed', notify user via WhatsApp (using `twilio` helper).

## Dev Notes

- **Architecture:** "Async Brain" pattern. The Ingestion (TS) handles the input, this story starts the Processing (Agent) logic in Python.
- **State Transitions:**
  - `pending` (webhook) -> `processing` (worker start) -> `pending` (classified, ready for extraction)
  - `processing` -> `failed` (unsupported/error)
- **Constraints:** Twilio `MediaContentType` values: `image/jpeg`, `image/png`, `video/mp4`, etc.
- **Testing:** Unit tests for regex patterns are critical. Mock the Twilio webhook payload for different scenarios (Link vs Photo vs Video).

### Project Structure Notes

- **Agent Source:** `agent/src/nodes/classifier.py`
- **Database:** `supabase/migrations/`
- **Naming:** Follow `snake_case` for DB fields: `content_type`.

### References

- [Architecture: Data Architecture](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md#data-architecture)
- [PRD: Metadata Extraction](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/prd.md#2-metadata-extraction-the-brain)
- [Twilio: Media Content Types](https://www.twilio.com/docs/whatsapp/api#media-content-types)

## Dev Agent Record

### Agent Model Used

Claude 4.5 Sonnet (dev-story implementation)

### Debug Log References

- Test execution: All 11 unit tests passed successfully
- YouTube regex validation: Fixed test to use proper 11-character video ID format

### Completion Notes List

- ✅ Created database migrations for `content_type` and `platform` fields with CHECK constraints
- ✅ Implemented atomic job claiming using PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` pattern
- ✅ Built ContentClassifier class with regex-based platform detection for YouTube, Instagram, TikTok, Udemy, and Coursera
- ✅ Implemented ClassifierWorker with job processing loop and Twilio notification on failure
- ✅ Created comprehensive unit tests covering all content types and platform patterns (11 tests, 100% pass rate)
- ✅ Added Python dependencies: supabase, twilio, python-dotenv

### File List

**Database Migrations:**
- `supabase/migrations/20260205000000_add_content_type_to_jobs.sql`
- `supabase/migrations/20260205000001_add_claim_job_function.sql`

**Agent Implementation:**
- `agent/src/nodes/classifier.py`
- `agent/src/worker.py`
- `agent/src/__init__.py`
- `agent/src/nodes/__init__.py`
- `agent/requirements.txt`

**Tests:**
- `agent/tests/test_classifier.py`
- `agent/tests/__init__.py`
