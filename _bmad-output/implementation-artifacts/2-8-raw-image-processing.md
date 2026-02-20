# Story 2.8: Raw Image Processing

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to send a photo to the bot,
so that I can capture visual information (receipts, fliers, menus) without typing.

## Acceptance Criteria

1. **Given** a WhatsApp Image message (MIME type image/jpeg, image/png)
2. **When** the Image Worker processes it
3. **Then** it MUST download the image from the Twilio Media URL
4. **And** Send the image to the Vision API (Story 2.1)
5. **And** Use a prompt to "Describe this image in detail and extract key information (text, objects, context)."
6. **And** Store the resulting description in the `summary` field of the `link_metadata` table (as `ai_summary`)
7. **And** Support processing multiple images in a single message if applicable
8. **And** (Optional) Save the image to Supabase Storage (`user_uploads` bucket) for long-term retention and update the `thumbnail_url` or similar field

## Tasks / Subtasks

- [x] **Implement Twilio Media Extractor** (AC: 1, 3)
  - [x] Create `agent/src/tools/image/extractors/twilio.py`
  - [x] Implement `TwilioExtractor` for raw media URLs
  - [x] Integrate with `ImageExtractorService` (route unknown/generic URLs)
- [x] **Implement Image Downloader Tool** (AC: 3)
  - [x] Create `agent/src/tools/image/downloader.py`
  - [x] Handle Twilio Basic Auth (Account SID + Auth Token) for media downloads
  - [x] Support byte-stream extraction for the Vision API
- [x] **Enhance Image Processor Node** (AC: 4, 5)
  - [x] Ensure `ImageProcessorNode` correctly handles the raw image bytes from the extractor
  - [x] Verify vision prompt alignment with story requirements
- [ ] **Implement Storage Persistence (Optional)** (AC: 8)
  - [ ] Add `agent/src/tools/image/storage.py` for Supabase Storage integration
  - [ ] Upload raw images to `user_uploads` bucket
  - [ ] Store permanent URL in `link_metadata.thumbnail_url`
- [x] **Testing**
  - [x] Unit tests for `TwilioExtractor` and `ImageDownloader`
  - [x] Integration test with mock Twilio Media URLs

## Dev Notes

### Architecture Patterns & Constraints

- **Async Brain Pattern:** The `ImageWorker` already polls for `content_type='image'`.
- **Extractor Pattern:** Follow the pattern in `agent/src/tools/image/service.py` to add a new extractor.
- **Library Requirements:** `Pillow` for image validation/thumbnail generation (already in `requirements.txt`). `httpx` for downloads.

### Project Structure Notes

**New Files:**
- `agent/src/tools/image/extractors/twilio.py`
- `agent/src/tools/image/downloader.py`
- `agent/src/tools/image/storage.py` (Optional)

**Modified Files:**
- `agent/src/tools/image/service.py` (Add routing logic)
- `agent/src/tools/image/__init__.py`

### Git Intelligence & Previous Learnings

- **From Story 2.4:** The `ImageWorker` is already capable of handling `MediaUrl0` if the classifier identifies it as an image.
- **From Story 2.1:** `VisionService` is the unified tool for image analysis.

### References

- **Architecture:** [architecture.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md)
- **Vision Tool:** `agent/src/tools/vision/service.py`
- **Image Service:** `agent/src/tools/image/service.py`

## Dev Agent Record

### Agent Model Used

Antigravity (BMAD Core 6.0 Engine)

### Debug Log References

### Completion Notes List

- Generated comprehensive story context for Raw Image Processing.
- Identified the need for `TwilioExtractor`.
- Documented Twilio Auth requirements for media downloads.

### File List

- [NEW] `agent/src/tools/image/extractors/twilio.py`
- [NEW] `agent/src/tools/image/downloader.py`
- [MODIFY] `agent/src/tools/image/service.py`
- [MODIFY] `agent/src/image_worker.py`
- [MODIFY] `agent/src/nodes/image_processor.py`
- [NEW] `agent/tests/test_twilio_tools.py`
- [NEW] `agent/tests/test_image_worker_integration.py`

## Senior Developer Review (AI)

- Found that tasks were completed but not marked. Fixed automatically.
- Found missing integration tests for the ImageWorker. Created `test_image_worker_integration.py`.
- Found undocumented file modifications in the worker and processor. Added them to the File List.
