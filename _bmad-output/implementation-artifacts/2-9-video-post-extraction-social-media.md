# Story 2.9: Video Post Extraction (Social Media)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want the bot to "watch" the Instagram Reels, TikToks, and YouTube Shorts I send,
so that I can get a detailed summary of the video content, not just the caption.

## Acceptance Criteria

1. **Given** a URL from Instagram, TikTok, or YouTube (Shorts/Video)
2. **When** the Scraper Node processes it
3. **Then** it MUST download the video content using `yt-dlp` (cookie compliant)
4. **And** Extract 3-5 distinct keyframes (Reusing Story 2.3 logic)
5. **And** Send these frames to the Vision API (Story 2.1)
6. **And** Aggregate the frame descriptions into a single "Video Content Summary"
7. **And** Combine this with the platform metadata (Title, Author, Caption from Story 2.2)
8. **And** Handle standard video duration limits (e.g. process only first 2 minutes if long)

## Tasks / Subtasks

- [ ] **Define Data Contracts** (AC: 6, 7)
  - [ ] Update `VideoProcessingRequest` (Story 2.3) to support `video_path` (local file) vs `video_url`
  - [ ] Ensure `ScraperResponse` can handle/merge `visual_summary` field
- [ ] **Enhance Scraper Node** (AC: 1, 3)
  - [ ] Update `agent/src/nodes/scraper.py` (Story 2.2) to support video download mode
  - [ ] Use `yt-dlp` to download video to temp path
  - [ ] Handle cookies/auth if needed for specific platforms (IG often requires it)
- [ ] **Integrate Video Processor** (AC: 4, 5, 6)
  - [ ] Reuse `VideoFrameExtractor` (Story 2.3) on the downloaded temp file
  - [ ] Reuse `VisionService` (Story 2.1) for frame analysis
  - [ ] Generate summary
- [ ] **Cleanup**
  - [ ] Delete temp video file after processing to save space
- [ ] **Testing**
  - [ ] Integration test with a public YouTube Short URL
  - [ ] Mock test for `yt-dlp` download failure

## Dev Notes

### Architecture Patterns & Constraints

- **Location:** `agent/src/nodes/scraper.py` (Enhancement) + resizing logic from `agent/src/tools/video/processor.py` (Story 2.3)
- **Library:** `yt-dlp` (Already in requirements for Story 2.2).
- **Video Logic:** Reuse strictly from Story 2.3 tool. Do not duplicate OpenCV logic.

### Project Structure Notes

**Refactoring Opportunity:**
- Ensure `VideoFrameExtractor` in `agent/src/tools/video/processor.py` is reusable (accepts a file path).
- `VisionService` is already reusable.

### Latest Technical Information

- **Instagram/TikTok Downloads:** heavily rate-limited or require cookies.
  - *Mitigation:* Use `yt-dlp` with `--cookies-from-browser` locally for dev, or valid cookies file in prod.
  - *Fallback:* If download fails, fall back to Story 2.2 (Metadata only) and add a note "Visual analysis failed due to platform restrictions".

### References

- **Story 2.2 (Scraper):** [2-2-youtube-social-link-scraper.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/implementation-artifacts/2-2-youtube-social-link-scraper.md)
- **Story 2.3 (Video Tool):** [2-3-video-frame-extraction.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/implementation-artifacts/2-3-video-frame-extraction.md)

## Dev Agent Record

### Agent Model Used

Claude 3.7 Sonnet (Anthropic)

### Debug Log References

No issues.

### Completion Notes List

- Created Story 2.9 based on user request.
- Leverages existing tools from Story 2.2 and 2.3.

### File List

- `agent/src/nodes/scraper.py` (Modify)
- `agent/src/tools/video/processor.py` (Reuse)
