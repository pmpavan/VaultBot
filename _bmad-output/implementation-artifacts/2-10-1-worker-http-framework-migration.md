# Story 2.10.1: Worker HTTP Framework Migration

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Developer,
I want to wrap the existing worker logic in a lightweight HTTP framework (like FastAPI or Flask),
so that Cloud Run can trigger the worker on-demand via a webhook instead of the worker polling continuously.

## Acceptance Criteria

1. **Given** an existing Python worker script (e.g. `video_worker.py`, `scraper_worker.py`, `image_worker.py`, `article_worker.py`, `worker.py`) running a `while` loop
2. **When** the migration is applied
3. **Then** the `run_loop` MUST be replaced with an HTTP POST endpoint (e.g. `/process`)
4. **And** the endpoint MUST accept a JSON payload identifying the job ID or the data to process
5. **And** the application MUST listen on the `$PORT` environment variable required by Cloud Run
6. **And** the container MUST cleanly exit or scale to zero when no requests are active

## Tasks / Subtasks

- [x] Task 1: Initialize FastAPI Setup
  - [x] Add `fastapi` and `uvicorn` to `agent/requirements.txt`
  - [x] Create a base HTTP application structure that will be shared among workers or implemented individually for each worker.
- [x] Task 2: Migrate `scraper_worker.py`
  - [x] Remove `run_loop` polling mechanism.
  - [x] Create `/process` POST endpoint that accepts `{"job_id": "<uuid>"}`.
  - [x] Update `process_and_update` to operate on the specific `job_id` passed, or fetch it specifically if not locked.
- [x] Task 3: Migrate remaining workers
  - [x] Migrate `video_worker.py`.
  - [x] Migrate `image_worker.py`.
  - [x] Migrate `article_worker.py`.
  - [x] Migrate `worker.py` (Classifier).
- [x] Task 4: Update Dockerfiles and Deployment Scripts
  - [x] Ensure Dockerfiles use `uvicorn` to start the FastAPI app (e.g., `CMD ["uvicorn", "scraper_worker:app", "--host", "0.0.0.0", "--port", "8080"]`).
  - [x] Inject the `$PORT` environment variable dynamically.

## Dev Notes

- **Technical Context**: The current `run_loop` uses `while not shutdown_requested` and `time.sleep()`. This keeps the Cloud Run container running 24/7 causing unnecessary billing. By migrating to FastAPI, Cloud Run can scale down to zero when there are no incoming webhook payloads.
- **Job Claiming**: Since the webhook trigger (Story 2.10.2) will send a specific `job_id`, the worker doesn't need to "fetch and lock" the oldest pending job generically. Instead, it should query the exact `job_id`, verify its status is still `pending`, lock it, and process it.

### Project Structure Notes

- Keep the entry points (e.g., `scraper_worker.py`) as the main app files.
- You can instantiate the `FastAPI` app globally in these files: `app = FastAPI()`.

### References

- Architecture context: `docs/planning-artifacts/architecture.md`
- Previous polling implementation: `agent/src/scraper_worker.py` (lines ~315-335)

## Dev Agent Record

### Agent Model Used

Antigravity

### Debug Log References

N/A

### Code Review Fixes Applied (2026-02-23)

- **[CRITICAL]** Fixed runtime crash: `signal.signal()` was called inside `__init__` which runs in a FastAPI thread-pool thread, raising `ValueError`. Moved to module-level `_handle_shutdown` function registered in the `lifespan` context (main thread).
- **[CRITICAL]** Fixed performance flaw: Worker class was instantiated per-request (re-initialising Supabase, Twilio, LangGraph on every webhook). Replaced with a FastAPI `lifespan`-managed module-level singleton `_worker`; endpoints now guard with a 503 if the singleton is `None`.
- **[CRITICAL]** Created `agent/tests/test_http_workers.py` — the file was claimed in Completion Notes but did not exist. Now contains 17 TestClient tests covering success (200), missing job (404), processing failure (500), and uninitialised worker (503) for all 5 workers.
- **[MEDIUM]** Removed all `run_loop`, `shutdown_requested`, and `_handle_shutdown` dead code from all 5 workers.
- **[MEDIUM]** Removed duplicate `from supabase import create_client, Client` import and duplicate dict-key declarations in `worker.py`.
- **[BONUS]** Fixed duplicate dict keys `auth_token` / `video_summary` in `video_worker.py` state construction.
- **[BONUS]** Fixed undefined variables `msg` in `video_worker.notify_user_success`, `message` in `article_worker.notify_user_success` and `worker.notify_user_failure`.
- **[BONUS]** Added missing `hashlib` import in `article_worker.py`.

### Code Review Fixes Applied — Round 2 (2026-02-23)

- **[MEDIUM]** Normalised Python base image: `Dockerfile.video`, `Dockerfile.image`, `Dockerfile.article`, `Dockerfile.classifier` changed from pre-release `python:3.14-slim` to stable `python:3.11-slim` — matching `Dockerfile.scraper` for consistency.
- **[LOW]** Added `job_id` input validation: `ProcessRequest` in all 5 workers now uses `job_id: str = Field(..., min_length=1)` — empty strings now return HTTP 422 before hitting Supabase.
- **[LOW]** Added 3 new test cases to `test_http_workers.py`: `TestInputValidation` (empty job_id → 422, missing job_id → 422) and `TestLifespanStartupFailure` (worker `__init__` failure propagates from lifespan).

### File List

- `agent/requirements.txt`
- `agent/src/scraper_worker.py`
- `agent/src/video_worker.py`
- `agent/src/image_worker.py`
- `agent/src/article_worker.py`
- `agent/src/worker.py`
- `agent/tests/test_http_workers.py`
- Dockerfiles inside `agent/`
