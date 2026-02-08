# Story 2.8: Raw Image Processing

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to send a photo to the bot,
so that I can capture visual information (receipts, fliers, menus) without typing.

## Acceptance Criteria

1. **Given** a WhatsApp Image message (MIME type image/jpeg, image/png)
2. **When** the Ingestion Service processes it
3. **Then** it MUST download the image from Twilio Media URL
4. **And** Send the image to the Vision API (Story 2.1)
5. **And** Use a prompt to "Describe this image in detail and extract key information (text, objects, context)."
6. **And** Store the resulting description in the `summary` field of the `jobs` (or `items`) table
7. **And** Support processing multiple images in a single message if applicable
8. **And** (Optional) Save the image to Supabase Storage for long-term retention and update the `snapshot_url` or similar field

## Tasks / Subtasks

- [ ] **Define Data Contracts** (AC: 1, 6)
  - [ ] Update `Job` payload schema to handle `media_url` and `mime_type`
  - [ ] Define `ImageProcessingRequest` and `ImageProcessingResponse`
- [ ] **Implement Image Downloader** (AC: 3)
  - [ ] Create `ImageDownloader` tool/utility
  - [ ] Handle Twilio authentication if required for media URLs
  - [ ] Validate image format (JPEG/PNG/WEBP)
- [ ] **Implement Image Processor Node** (AC: 4, 5)
  - [ ] Create `agent/src/nodes/image_processor.py`
  - [ ] Integrate with `VisionService` (Story 2.1)
  - [ ] Construct appropriate prompt for general image analysis
  - [ ] Handle Vision API responses
- [ ] **Implement Storage Integration (Optional but Recommended)** (AC: 8)
  - [ ] Upload downloaded image to Supabase Storage bucket (`user_uploads`)
  - [ ] Get public/signed URL
  - [ ] Store this URL in the database instead of the ephemeral Twilio URL
- [ ] **Testing**
  - [ ] Mock tests for Image Processor Node
  - [ ] Live test with a sample image URL

## Dev Notes

### Architecture Patterns & Constraints

- **Location:** `agent/src/nodes/image_processor.py`
- **Tool Location:** `agent/src/tools/image/` (if complex logic needed)
- **Library:** `Pillow` (PIL) for image manipulation/validation. `httpx` or `requests` for downloading.
- **Visual API:** Reuse `VisionService` from Story 2.1.

### Project Structure Notes

**Recommended File Structure:**
```
agent/src/nodes/image_processor.py
agent/src/tools/image/
├── __init__.py
├── downloader.py       # Handles Twilio Media URL download
└── storage.py          # Handles Supabase Storage upload (if not generic)
```

**Dependency Updates:**
- Add `Pillow` to `agent/requirements.txt`
- Ensure `supabase` client is configured for Storage access

### Latest Technical Information

- **Twilio Media URLs:** require Basic Auth (Account SID + Auth Token) if "Enforce HTTP Basic Auth for Media Access" is enabled in Twilio Console. The agent should handle this if configured.
- **Supabase Storage:** Use `supabase-py` client `storage.from_('bucket').upload(...)`.

### References

- **Story 2.1:** [2-1-vision-api-integration.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/implementation-artifacts/2-1-vision-api-integration.md)
- **Architecture:** [architecture.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md)

## Dev Agent Record

### Agent Model Used

Claude 3.7 Sonnet (Anthropic)

### Debug Log References

No issues.

### Completion Notes List

- Created Story 2.8 based on user request.
- Added `Pillow` requirement note.

### File List

- `agent/src/nodes/image_processor.py`
- `agent/src/tools/image/downloader.py`
