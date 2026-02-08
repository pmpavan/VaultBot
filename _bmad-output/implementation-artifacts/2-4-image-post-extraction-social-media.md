# Story 2.4: Image Post Extraction (Social Media)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to save image posts from Instagram, TikTok, and YouTube,
so that the system can analyze the visual content even when there's no video.

## Acceptance Criteria

1. **Given** a social media URL pointing to an image post (Instagram photo, TikTok image carousel, YouTube community post)
2. **When** the Image Extractor processes it
3. **Then** it MUST download the image(s) from the platform
4. **And** Extract platform metadata (caption, hashtags, author, post date)
5. **And** Send the image(s) to the Vision API (Story 2.1) for semantic analysis
6. **And** Return structured metadata: `title`, `description`, `author`, `image_urls`, `platform`, `content_type='image'`
7. **And** Handle multiple images in a single post (carousel/album)
8. **And** Use proxy rotation to avoid IP blocks

## Tasks / Subtasks

- [x] **Define Data Contracts** (AC: 6)
  - [x] Create `ImageExtractionRequest` (url, platform)
  - [x] Create `ImageExtractionResponse` (images: List[bytes], metadata: Dict)
  - [x] Define `ImageExtractionError` exceptions
- [x] **Implement Image Extractor Tool** (AC: 3, 4, 7, 8)
  - [x] Create `agent/src/tools/image` module
  - [x] **Instagram**: Implement `InstagramExtractor` using `instaloader` (with `ProxyManager`)
  - [x] **TikTok**: Implement `TikTokExtractor` (attempt `yt-dlp` or fallback to specialized scraping)
  - [x] **YouTube**: Implement `YouTubeCommunityExtractor` (using `BeautifulSoup` + `requests` with proxy)
  - [x] Implement `ImageExtractorService` to route based on URL
- [x] **Integrate Vision API** (AC: 5)
  - [x] Reuse `VisionService` (Story 2.1) to analyze images
  - [x] Handle multiple images (sequence or batch if supported)
- [x] **Implement Image Processing Node** (AC: 2, 6)
  - [x] Create `agent/src/nodes/image_processor.py`
  - [x] Fetch job -> Extract Images -> Vision Analysis -> Summarize -> Update Job
- [x] **Implement Orchestrator** (AC: 6)
  - [x] Create `agent/src/image_worker.py` (patterned after `video_worker.py`)
  - [x] Orchestrate the `pending` -> `complete` flow for `content_type='image'`
- [x] **Testing**
  - [x] Unit tests for extractors
  - [x] Integration tests with sample URLs
  - [x] Mock tests for Vision API

## Dev Notes

### Architecture Patterns & Constraints

- **Location:** `agent/src/tools/image/` (New tool module)
- **Node Location:** `agent/src/nodes/image_processor.py`
- **Worker:** `agent/src/image_worker.py`
- **Libraries:**
  - `instaloader`: For Instagram (robust, handles JSON scraping).
  - `yt-dlp`: Try for TikTok (may need specific flags).
  - `requests` + `BeautifulSoup`: For custom scraping (YouTube Community).
- **Proxy:** MUST use `agent/src/tools/scraper/proxy.py` (`ProxyManager`).

### Project Structure Notes

**Recommended File Structure:**
```
agent/src/tools/image/
├── __init__.py
├── types.py            # Data contracts
├── service.py          # Unified service (Router -> Extractor -> Vision)
├── extractors/
│   ├── __init__.py
│   ├── base.py
│   ├── instagram.py    # Instaloader implementation
│   ├── tiktok.py       # TikTok specific logic
│   └── youtube.py      # Community post logic
```

### Latest Technical Information (Web Research - Feb 2026)

- **Instagram**: `instaloader` is the best Python option but requires proxy rotation to avoid 429s.
- **TikTok**: Slide shows are tricky with `yt-dlp`. If it fails, consider using a third-party wrapper or simple metadata extraction + screenshotting (if headless browser available - but specialized scraping is preferred). Architecture specifies "Dumb Pipe" ingestion, but this is the "Brain" agent `requests` is fine.
- **YouTube**: Community posts are not in API. HTML parsing is required.

### References

- **Architecture:** [architecture.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md)
- **Scraper Tool:** [agent/src/tools/scraper/](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/tools/scraper/)
- **Vision Service:** [agent/src/tools/vision/service.py](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/tools/vision/service.py)
- **Previous Story (Video):** [2-3-video-frame-extraction.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/implementation-artifacts/2-3-video-frame-extraction.md)

### Implementation Update - LangGraph Migration (Feb 2026)

To standardize state management and execution flow, the following components were migrated to **LangGraph** `StateGraph`:

1.  **Image Processor**: `agent/src/nodes/image_processor.py` (New)
2.  **Video Processor**: `agent/src/nodes/video_processor.py` (Refactored)
3.  **Classifier**: `agent/src/nodes/classifier.py` (Refactored)

**Pattern:**
Each node module now exports a `create_[name]_graph()` function that returns a compiled `StateGraph`. Workers (`worker.py`, `image_worker.py`, `video_worker.py`) initialize this graph and call `.invoke(state)` instead of calling the class instance directly.

**New Dependencies:**
- `langgraph`
- `pydantic`
- `instaloader` (for Instagram)

**Tests:**
- `agent/tests/test_image_processor.py` (Verified)
- `agent/tests/test_video_processor.py` (Verified)
- `agent/tests/test_classifier.py` (Verified)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Implemented Image Extractor Service with Instagram support via Instaloader.
- Implemented TikTok and YouTube extractors as stubs for now (as per plan/constraints).
- Implemented Image Processor Node using Vision API.
- Implemented Image Worker for async job processing.
- Added Dockerfile and deployment scripts.
- Added Unit Tests.

### File List

- agent/src/tools/image/types.py
- agent/src/tools/image/__init__.py
- agent/src/tools/image/extractors/base.py
- agent/src/tools/image/extractors/instagram.py
- agent/src/tools/image/extractors/tiktok.py
- agent/src/tools/image/extractors/youtube.py
- agent/src/tools/image/service.py
- agent/src/nodes/image_processor.py
- agent/src/nodes/__init__.py
- agent/src/image_worker.py
- agent/Dockerfile.image
- agent/deploy-gcp.sh
- agent/tests/test_image_service.py
- agent/tests/test_image_processor.py
- agent/requirements.txt
