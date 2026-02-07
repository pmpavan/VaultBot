# Story 2.2: Universal Link Scraper & Platform Router

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to save ANY link (social media, blogs, news articles, generic URLs),
So that the system can intelligently extract metadata based on the content type.

## Acceptance Criteria

1. **Given** ANY URL (social media, blog, news article, generic link)
2. **When** the Scraper Service processes it
3. **Then** it MUST detect the platform/content type (Instagram, TikTok, YouTube, Blog, News, Generic)
4. **And** It MUST route to the appropriate extraction strategy:
   - **Social Media (IG/TikTok/YouTube):** Use yt-dlp for video/image metadata
   - **Blog/News/Article:** Return URL for downstream text parser (Story 2.4+)
   - **Generic URL:** Extract basic OpenGraph metadata (title, description, image)
5. **And** It MUST return standardized metadata: `title`, `description`, `author`, `content_type`, `thumbnail_url`, `platform`, `extraction_strategy`
6. **And** It MUST use a proxy service to avoid IP blocks (for social media scraping)
7. **And** It MUST handle private/expired video errors by returning a specific error code
8. **And** It MUST support graceful degradation (return partial metadata if some fields unavailable)
9. **And** It MUST implement retry logic with exponential backoff for transient failures

## Tasks / Subtasks

- [x] **Define Data Contracts** (AC: 5)
  - [x] Create `ScraperRequest` Pydantic model (url, platform_hint)
  - [x] Create `ScraperResponse` Pydantic model (title, description, author, content_type, thumbnail_url, platform, extraction_strategy, raw_url)
  - [x] Define `ExtractionStrategy` enum ('ytdlp', 'opengraph', 'passthrough')
  - [x] Define `ContentType` enum ('video', 'image', 'article', 'link')
  - [x] Define standardized `ScraperError` exceptions (PrivateVideoError, ExpiredVideoError, UnsupportedPlatformError, ProxyError)
- [x] **Implement Platform Detection & Router** (AC: 3, 4)
  - [x] Create `PlatformDetector` class with URL pattern matching
  - [x] Detect social media platforms: Instagram, TikTok, YouTube (route to yt-dlp)
  - [x] Detect blog/news domains (route to passthrough for downstream text parser)
  - [x] Detect generic URLs (route to OpenGraph extractor)
  - [x] Return platform type and recommended extraction strategy
- [x] **Implement yt-dlp Adapter** (AC: 4, 8)
  - [x] Create `YtDlpAdapter` class with extract_info wrapper
  - [x] Configure yt-dlp options for metadata-only extraction (no download)
  - [x] Implement field mapping from yt-dlp output to ScraperResponse
  - [x] Handle missing fields gracefully (partial metadata support)
  - [x] Set `extraction_strategy='ytdlp'` in response
- [x] **Implement OpenGraph Extractor** (AC: 4)
  - [x] Create `OpenGraphExtractor` class for generic URLs
  - [x] Parse HTML for og:title, og:description, og:image meta tags
  - [x] Fallback to <title> and <meta description> if OpenGraph missing
  - [x] Set `extraction_strategy='opengraph'` in response
- [x] **Implement Passthrough Handler** (AC: 4)
  - [x] Create `PassthroughHandler` for blog/news URLs
  - [x] Return minimal metadata (URL, detected platform)
  - [x] Set `extraction_strategy='passthrough'` to signal downstream text parser needed
  - [x] Add note in response indicating full text extraction pending
- [x] **Implement Proxy Integration** (AC: 6)
  - [x] Research and select proxy provider (Bright Data, Oxylabs, or Swiftproxy recommended)
  - [x] Configure yt-dlp to use rotating proxies (only for social media)
  - [x] Implement proxy credential management via environment variables
  - [x] Add proxy health check and fallback logic
- [x] **Implement Unified Scraper Service** (AC: 3, 9)
  - [x] Create `ScraperService` class with `scrape(request: ScraperRequest) -> ScraperResponse`
  - [x] Implement routing logic based on platform detection
  - [x] Implement retry logic using `tenacity` library (matching Story 2.1 pattern)
  - [x] Add timeout handling (30s default per request)
- [x] **Error Handling & Edge Cases** (AC: 7, 8)
  - [x] Detect and classify private video errors
  - [x] Detect and classify expired/deleted video errors
  - [x] Implement fallback for geo-restricted content
  - [x] Handle malformed URLs gracefully
  - [x] Add logging for debugging failed scrapes
- [x] **Integration Tests** (AC: All)
  - [x] Create live tests with social media URLs (Instagram, TikTok, YouTube)
  - [x] Create tests with blog/news URLs (passthrough strategy)
  - [x] Create tests with generic URLs (OpenGraph extraction)
  - [x] Create mock tests for error scenarios (private, expired, proxy failure)
  - [x] Test graceful degradation scenarios

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document:**
- **Location:** `agent/src/tools/` (Tools pattern established in Story 2.1)
- **Language:** Python (Agent layer uses Python per architecture)
- **Adapter Pattern:** Follow the same adapter pattern used in Vision API (Story 2.1)
- **Error Handling:** Standardized exceptions (matching VisionError pattern from 2.1)
- **Retry Logic:** Use `tenacity` library (already in requirements.txt from Story 2.1)

**Key Architecture Requirements:**
- **Proxy Dependence:** "Scrapers rely on rotating residential proxies to avoid blocks" (Architecture.md line 43)
- **Reliability:** NFR-05 requires ">90% success rate" with proxy rotation
- **Dead Letter Queue:** Failed scrapes must route to DLQ (Story 1.5 integration point)

### Project Structure Notes

**Recommended File Structure:**
```
agent/src/tools/scraper/
├── __init__.py
├── types.py              # ScraperRequest, ScraperResponse, ExtractionStrategy, ContentType
├── service.py            # Main ScraperService with routing logic
├── detector.py           # PlatformDetector for URL classification
├── extractors/
│   ├── __init__.py
│   ├── ytdlp.py         # YtDlpExtractor for social media
│   ├── opengraph.py     # OpenGraphExtractor for generic URLs
│   └── passthrough.py   # PassthroughHandler for blog/news
└── proxy/
    └── manager.py        # Proxy configuration and health checks
```

**Alignment with Unified Project Structure:**
- Follows `agent/src/tools/` pattern from Architecture.md line 246
- Mirrors the structure established in Story 2.1 (`agent/src/tools/vision/`)
- Maintains separation of concerns: types, service, adapters

### Previous Story Intelligence (Story 2.1: Vision API Integration)

**Key Learnings to Apply:**
1. **Pydantic Models:** Use strict Pydantic models for request/response (prevents "stringly typed" JSON)
2. **Adapter Pattern:** Separate provider-specific logic into adapters (enables future provider swaps)
3. **Tenacity for Retries:** Use `tenacity` library with exponential backoff (already in requirements.txt)
4. **Error Normalization:** Create custom exception hierarchy for standardized error handling
5. **Environment Variables:** Use `.env` for credentials (pattern: `PROXY_USERNAME`, `PROXY_PASSWORD`)

**Files Created in Story 2.1 (Reference Pattern):**
- `agent/src/tools/vision/types.py` - Data contracts
- `agent/src/tools/vision/service.py` - Main service class
- `agent/src/tools/vision/providers/openrouter.py` - Provider adapter
- `tests/tools/vision/test_service_mock.py` - Mock tests

**Code Patterns to Replicate:**
- Service class with single public method: `scrape(request) -> response`
- Adapter classes with consistent interface
- Mock tests using `pytest` (avoid expensive API calls in CI)

### Latest Technical Information (Web Research - Feb 2026)

**yt-dlp Library (Social Media Extraction):**
- **Latest Version:** `yt-dlp==2026.02.04` (released Feb 4, 2026)
- **Python Compatibility:** Requires Python 3.10+
- **Platform Support:**
  - YouTube: Full support (may require `yt-dlp-ejs` for some features)
  - Instagram: Supported
  - TikTok: Supported (occasional API changes require latest version)
- **Installation:** `pip install yt-dlp==2026.02.04`
- **Key Features for This Story:**
  - Metadata extraction without downloading video
  - Proxy support via `--proxy` option
  - JSON output format for easy parsing
  - Error codes for private/expired videos

**OpenGraph Parser (Generic URL Extraction):**
- **Recommended Library:** `beautifulsoup4` + `requests` (already common in Python projects)
- **Alternative:** `opengraph-py3` for dedicated OpenGraph parsing
- **Fallback Strategy:** Parse `<title>`, `<meta name="description">` if no OG tags
- **Use Case:** Blog posts, news articles, generic websites without yt-dlp support

**URL Pattern Detection:**
- **Social Media Patterns:**
  - Instagram: `instagram.com/p/`, `instagram.com/reel/`, `instagram.com/tv/`
  - TikTok: `tiktok.com/@*/video/`, `vm.tiktok.com/`
  - YouTube: `youtube.com/watch`, `youtu.be/`, `youtube.com/shorts/`
- **Blog/News Indicators:** Common blog platforms (Medium, Substack, WordPress), news domains
- **Generic Fallback:** Any URL not matching above patterns

**Proxy Services (2026 Recommendations):**
- **Top Choices:**
  1. **Bright Data:** 150M+ IPs, 195 countries, enterprise-grade
  2. **Oxylabs:** 175M+ IPs, automated rotation, city-level targeting
  3. **Swiftproxy:** 80M+ ethically sourced IPs, high reliability
- **Best Practices:**
  - Use per-request rotation for scraping tasks
  - Implement backoff on 429 (rate limit) errors
  - Monitor success rates and switch providers if <90%
  - Use residential proxies (not datacenter) to avoid detection
- **Python Integration:**
  ```python
  proxies = {
      'http': 'http://user:pass@proxy.provider.com:port',
      'https': 'http://user:pass@proxy.provider.com:port'
  }
  ```

**yt-dlp Configuration for Metadata Extraction:**
```python
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,  # Get full metadata
    'skip_download': True,  # Don't download video
    'proxy': proxy_url,     # Rotating proxy
    'socket_timeout': 30,   # Prevent hanging
}
```

### Testing Standards

**From Architecture & Story 2.1:**
- Use `pytest` for all tests
- Create separate test files for live vs mock tests:
  - `tests/tools/scraper/test_service_mock.py` - Fast, no network calls
  - `scripts/test_scraper_live.py` - Manual testing with real URLs
- Mock external dependencies (yt-dlp, proxy) in unit tests
- Use `pytest-vcr` or similar for recording/replaying HTTP interactions

**Test Coverage Requirements:**
- Happy path for each platform (YouTube, Instagram, TikTok)
- Error scenarios (private, expired, unsupported platform)
- Proxy failure and retry logic
- Graceful degradation (partial metadata)

### Integration Points

**Upstream (Story 1.3: Payload Parser & Classification):**
- Receives classified jobs with `content_type='link'` and `platform` hint
- Job payload contains the URL to scrape

**Downstream (Future Stories):**
- Scraped metadata feeds into Story 2.4 (Data Normalizer Agent)
- Scraped metadata used in Story 2.5 (Natural Language Summary Generator)
- Failed scrapes route to Story 1.5 (Dead Letter Queue)

**Database Integration:**
- Update `jobs` table with scraped metadata
- Store `thumbnail_url` for later use in Story 3.4 (Dynamic Card Generator)

### Database Schema & Deduplication

**CRITICAL ARCHITECTURAL DECISION:**

VaultBot uses a **two-table design** for link metadata:

1. **`link_metadata`** (Public, Deduplicated)
   - One row per unique URL (identified by `url_hash`)
   - Stores: title, description, thumbnail, platform, content_type, extraction_strategy
   - AI fields: ai_summary, normalized_category, normalized_tags (populated by Stories 2.6, 2.7)
   - Vector embedding for semantic search (Epic 3)
   - **No RLS** - this is public data

2. **`user_saved_links`** (Private, User Attribution)
   - Tracks who saved what link, in which context (DM vs Group)
   - Stores: link_id (FK), user_id, source_channel_id, source_type, attributed_user_id
   - **RLS enabled** - users only see their own saves + group saves

**Deduplication Flow (MUST IMPLEMENT):**

```python
# Pseudocode for Story 2.2 implementation
async def process_link_job(job: Job):
    url = extract_url_from_payload(job.payload)
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    
    # Step 1: Check if URL already exists
    existing = await supabase.table('link_metadata') \
        .select('*') \
        .eq('url_hash', url_hash) \
        .single()
    
    if existing and existing['scrape_status'] == 'scraped':
        # URL exists - skip scraping, increment counter
        link_id = existing['id']
        await supabase.table('link_metadata') \
            .update({'scrape_count': existing['scrape_count'] + 1}) \
            .eq('id', link_id)
    else:
        # New URL - scrape it
        metadata = await scraper_service.scrape(url)
        
        # Insert into link_metadata (public table)
        result = await supabase.table('link_metadata').insert({
            'url': url,
            'url_hash': url_hash,
            'platform': metadata.platform,
            'content_type': metadata.content_type,
            'extraction_strategy': 'ytdlp',  # or 'opengraph', 'passthrough'
            'title': metadata.title,
            'description': metadata.description,
            'author': metadata.author,
            'thumbnail_url': metadata.thumbnail_url,
            'duration': metadata.duration,
            'scrape_status': 'scraped'
        })
        link_id = result['id']
    
    # Step 2: Always create user_saved_links entry (private table)
    await supabase.table('user_saved_links').insert({
        'link_id': link_id,
        'user_id': job.user_id,
        'source_channel_id': job.source_channel_id,
        'source_type': job.source_type,
        'attributed_user_id': job.user_id  # Who shared it
    })
```

**Why This Matters:**
- **Efficiency:** Same YouTube video saved by 10 users = 1 scrape, not 10
- **Consistency:** Everyone sees the same metadata for the same link
- **Privacy:** User attribution is separate from public metadata
- **Search:** Group members can discover links saved by others in the group

### Environment Variables Required

Add to `.env` and `.env.example`:
```bash
# Proxy Configuration (Story 2.2)
PROXY_PROVIDER=brightdata  # or oxylabs, swiftproxy
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
PROXY_HOST=proxy.provider.com
PROXY_PORT=22225

# yt-dlp Configuration
YTDLP_TIMEOUT=30  # seconds
```

### Dependencies to Add

Update `agent/requirements.txt`:
```
# Story 2.2: YouTube & Social Link Scraper
yt-dlp==2026.02.04
```

**Note:** `tenacity` already added in Story 2.1, no need to duplicate.

### References

- **Architecture:** [architecture.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md#L246) (Tools: `agent/src/tools/`)
- **Epic 2 Requirements:** [epics.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/epics.md#L186-L199) (Story 2.2 details)
- **Previous Story Pattern:** [2-1-vision-api-integration.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/implementation-artifacts/2-1-vision-api-integration.md) (Adapter pattern reference)
- **yt-dlp Documentation:** [GitHub - yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Proxy Best Practices:** [SwiftProxy - Rotating Residential Proxies 2026](https://swiftproxy.net/)

## Dev Agent Record

### Agent Model Used

Claude 3.7 Sonnet (Anthropic)

### Debug Log References

No critical debug issues encountered. Implementation followed Story 2.1 patterns successfully.

### Completion Notes List

✅ **Data Contracts Implemented** (2026-02-07)
- Created Pydantic models: `ScraperRequest`, `ScraperResponse`
- Defined enums: `ExtractionStrategy` (ytdlp, opengraph, passthrough, vision), `ContentType` (video, image, article, link)
- Implemented custom exception hierarchy: `ScraperError` base class with specific error types (PrivateVideoError, ExpiredVideoError, GeoRestrictedError, UnsupportedPlatformError, ProxyError)

✅ **Platform Detection & Routing** (2026-02-07)
- Implemented `PlatformDetector` with regex pattern matching for Instagram, TikTok, YouTube
- Added blog/news platform detection (Medium, Substack, WordPress, major news sites)
- Generic URL fallback to OpenGraph extraction
- Returns tuple of (platform, content_type, extraction_strategy)

✅ **Extractors Implemented** (2026-02-07)
- **YtDlpExtractor**: Social media extraction with yt-dlp, proxy support, error classification (private/expired/geo-restricted), graceful degradation for missing fields
- **OpenGraphExtractor**: Generic URL extraction with OpenGraph tags, fallback to standard HTML meta tags
- **PassthroughHandler**: Minimal metadata for blog/news URLs, signals downstream text extraction needed (Story 2.5)

✅ **Proxy Integration** (2026-02-07)
- Created `ProxyManager` with environment variable configuration (PROXY_PROVIDER, PROXY_USERNAME, PROXY_PASSWORD, PROXY_HOST, PROXY_PORT)
- Integrated with yt-dlp for social media scraping only
- Health check placeholder for future enhancement

✅ **Unified Scraper Service** (2026-02-07)
- Implemented `ScraperService` as main entry point following Story 2.1 pattern
- Routing logic based on platform detection
- Retry logic using `tenacity` library with exponential backoff (3 attempts, 2-10s wait)
- Timeout handling (30s default, configurable via YTDLP_TIMEOUT)

✅ **Error Handling** (2026-02-07)
- Error classification in yt-dlp adapter (private, expired, geo-restricted)
- Graceful degradation for partial metadata (AC: 8)
- Comprehensive logging for debugging

✅ **Testing** (2026-02-07)
- Created unit tests for data contracts (`test_types.py`)
- Created mock tests for service (`test_service_mock.py`) - routing, error handling, retry logic
- Created live integration test script (`scripts/test_scraper_live.py`) for manual testing

✅ **Dependencies Added** (2026-02-07)
- yt-dlp>=2024.12.23 (flexible version for latest updates)
- beautifulsoup4==4.12.3
- requests==2.31.0
- lxml==5.1.0 (for faster HTML parsing)

✅ **Code Review Fixes Applied** (2026-02-07)
- **Proxy Health Check**: Replaced TODO with actual HTTP connectivity test using httpbin.org
- **Domain Detection Security**: Fixed brittle substring matching to use exact domain matching (prevents 'medium.com.evil.site' false positives)
- **Configurable Timeouts**: Added OPENGRAPH_TIMEOUT environment variable for consistency
- **User-Agent Flexibility**: Made User-Agent configurable in OpenGraphExtractor
- **Parser Performance**: Switched from html.parser to lxml for faster BeautifulSoup parsing
- **Automated Integration Tests**: Created comprehensive test suite with pytest markers for CI/CD

### File List

**New Files Created:**
- `agent/src/tools/scraper/__init__.py` - Module exports
- `agent/src/tools/scraper/types.py` - Data contracts (Pydantic models, enums, exceptions)
- `agent/src/tools/scraper/detector.py` - Platform detection and routing
- `agent/src/tools/scraper/service.py` - Unified scraper service with retry logic
- `agent/src/tools/scraper/extractors/__init__.py` - Extractors module
- `agent/src/tools/scraper/extractors/ytdlp.py` - yt-dlp adapter for social media
- `agent/src/tools/scraper/extractors/opengraph.py` - OpenGraph extractor for generic URLs
- `agent/src/tools/scraper/extractors/passthrough.py` - Passthrough handler for blog/news
- `agent/src/tools/scraper/proxy/__init__.py` - Proxy module
- `agent/src/tools/scraper/proxy/manager.py` - Proxy configuration manager
- `agent/tests/tools/scraper/test_types.py` - Unit tests for data contracts
- `agent/tests/tools/scraper/test_service_mock.py` - Mock tests for service
- `agent/tests/tools/scraper/test_integration.py` - Automated integration tests (NEW)
- `scripts/test_scraper_live.py` - Live integration test script
- `pytest.ini` - Pytest configuration with test markers (NEW)

**Modified Files:**
- `agent/requirements.txt` - Added yt-dlp, beautifulsoup4, requests, lxml dependencies
- `agent/src/tools/scraper/proxy/manager.py` - Implemented real health check (CODE REVIEW FIX)
- `agent/src/tools/scraper/detector.py` - Fixed domain detection security issue (CODE REVIEW FIX)
- `agent/src/tools/scraper/service.py` - Added configurable OpenGraph timeout (CODE REVIEW FIX)
- `agent/src/tools/scraper/extractors/opengraph.py` - Added user-agent parameter, lxml parser (CODE REVIEW FIX)
- `supabase/migrations/20260206000002_enable_pgvector.sql` - Enabled pgvector extension
- `supabase/migrations/20260207000000_create_link_metadata_table.sql` - Created link_metadata table
- `supabase/migrations/20260207000001_create_user_saved_links_table.sql` - Created user_saved_links table
