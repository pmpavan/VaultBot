# Story 2.5: Text & Article Parser

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a User,
I want to save links to blog posts, news articles, and text-based content,
so that I can search through written content later.

## Acceptance Criteria

1. **Given** a URL pointing to a blog post, news article, or generic web page
2. **When** the Text Parser processes it
3. **Then** it MUST extract the main article text (removing ads, navigation, footers)
4. **And** Extract metadata: `title`, `author`, `publish_date`, `site_name`
5. **And** Extract OpenGraph tags if available (og:title, og:description, og:image)
6. **And** Return the full text content for downstream summarization (Story 2.7)
7. **And** Handle paywalled content gracefully (extract what's available, mark as partial)
8. **And** Detect and classify content type: 'article', 'blog', 'documentation', 'generic'

## Tasks / Subtasks

- [x] **Define Data Contracts** (AC: 4, 5, 6, 8)
  - [x] Create `ArticleExtractionRequest` (url, content_type_hint)
  - [x] Create `ArticleExtractionResponse` (text, metadata, og_tags, content_classification)
  - [x] Define `ArticleExtractionError` exceptions
- [x] **Implement Article Extractor Tool** (AC: 3, 4, 5, 7, 8)
  - [x] Create `agent/src/tools/article` module
  - [x] Implement `ArticleExtractor` using `trafilatura` (primary) with `newspaper4k` fallback
  - [x] Implement OpenGraph parser using `BeautifulSoup` + `meta-tags-parser`
  - [x] Implement content classifier (article/blog/documentation/generic)
  - [x] Add paywall detection and graceful handling
  - [x] Integrate `ProxyManager` for HTTP requests
- [x] **Implement Article Processing Node** (AC: 2, 6)
  - [x] Create `agent/src/nodes/article_processor.py`
  - [x] Fetch job → Extract Article → Classify → Update Job
- [x] **Implement Orchestrator** (AC: 6)
  - [x] Create `agent/src/article_worker.py` (patterned after `image_worker.py`)
  - [x] Orchestrate the `pending` → `complete` flow for `content_type='link'` (non-social)
- [x] **Testing**
  - [x] Unit tests for article extractor
  - [x] Integration tests with sample URLs (news, blog, documentation)
  - [x] Mock tests for proxy and network failures

## Dev Notes

### Architecture Patterns & Constraints

- **Location:** `agent/src/tools/article/` (New tool module)
- **Node Location:** `agent/src/nodes/article_processor.py`
- **Worker:** `agent/src/article_worker.py`
- **Libraries:**
  - `trafilatura`: Primary article extraction (best precision/recall balance, supports multiple output formats)
  - `newspaper4k`: Fallback for news articles (maintained fork of newspaper3k, better multilingual support)
  - `BeautifulSoup` + `lxml`: For OpenGraph tag parsing and HTML processing
  - `requests`: For HTTP requests with proxy support
- **Proxy:** MUST use `agent/src/tools/scraper/proxy.py` (`ProxyManager`)
- **Pattern:** Follow the same architecture as Story 2.4 (Image Extraction) - modular extractors with unified service

### Project Structure Notes

**Recommended File Structure:**
```
agent/src/tools/article/
├── __init__.py
├── types.py            # Data contracts (Request, Response, Errors)
├── service.py          # Unified service (Router → Extractor → Classifier)
├── extractors/
│   ├── __init__.py
│   ├── base.py         # Base extractor interface
│   ├── trafilatura_extractor.py    # Primary extractor
│   ├── newspaper_extractor.py      # Fallback extractor
│   └── opengraph_parser.py         # OpenGraph metadata parser
└── classifier.py       # Content type classifier
```

### Latest Technical Information (Web Research - Feb 2026)

**Article Extraction Libraries (2026 Best Practices):**

1. **Trafilatura** (Primary Choice):
   - **Why:** Best balance of precision and recall according to 2026 benchmarks
   - **Strengths:** Robust extraction, preserves formatting, supports TXT/Markdown/JSON/XML output
   - **Limitations:** Struggles with JavaScript-rendered pages (not an issue for our use case)
   - **Usage:** Can process live URLs or pre-fetched HTML
   - **Version:** Latest stable (check PyPI for current version)

2. **Newspaper4k** (Fallback):
   - **Why:** Maintained fork of newspaper3k (original stalled in 2020)
   - **Strengths:** Excellent for news articles, multilingual support, NLP integration
   - **Usage:** Specialized for news content, good fallback when Trafilatura fails
   - **Version:** Use newspaper4k (NOT newspaper3k)

3. **BeautifulSoup + lxml**:
   - **Why:** Fast HTML parsing, required for OpenGraph tag extraction
   - **Usage:** Parse `<meta property="og:*">` tags from HTML head
   - **Performance:** lxml is faster than html.parser for large documents

**OpenGraph Metadata Extraction:**
- **Approach:** Use BeautifulSoup to find all `<meta>` tags with `property` starting with "og:"
- **Common Tags:** og:title, og:description, og:image, og:url, og:type, og:site_name
- **Fallback:** If OG tags missing, use standard meta tags (title, description) or extracted article metadata

**Proxy Integration:**
- **Pattern:** Reuse existing `ProxyManager` from `agent/src/tools/scraper/proxy/manager.py`
- **Usage:** Pass proxy URL to `requests` library: `requests.get(url, proxies={'http': proxy_url, 'https': proxy_url})`
- **Health Check:** ProxyManager has `health_check()` method for validation

**Content Classification Strategy:**
- **Article:** News sites, journalism (check domain patterns, publish_date presence)
- **Blog:** Personal/company blogs (check URL patterns like /blog/, author presence)
- **Documentation:** Technical docs (check domain patterns like docs.*, readthedocs.io)
- **Generic:** Fallback for unclassified content

**Paywall Handling:**
- **Detection:** Check for common paywall indicators (limited text length, specific CSS classes, subscription prompts)
- **Strategy:** Extract available content, mark as `partial: true` in metadata
- **User Feedback:** Return what's available with clear indication of paywall

### References

- **Architecture:** [architecture.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md#L244-L247)
- **PRD:** [prd.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/prd.md#L231-L246)
- **Epics:** [epics.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/epics.md#L231-L246)
- **Scraper Tool:** [agent/src/tools/scraper/](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/tools/scraper/)
- **Proxy Manager:** [agent/src/tools/scraper/proxy/manager.py](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/tools/scraper/proxy/manager.py)
- **Previous Story (Image):** [2-4-image-post-extraction-social-media.md](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/implementation-artifacts/2-4-image-post-extraction-social-media.md)

### Previous Story Intelligence (Story 2.4: Image Extraction)

**Key Learnings from Story 2.4:**

1. **Modular Extractor Pattern:**
   - Base extractor interface in `extractors/base.py`
   - Platform-specific extractors (Instagram, TikTok, YouTube)
   - Unified service layer for routing and orchestration
   - **Apply to 2.5:** Use same pattern with Trafilatura/Newspaper extractors

2. **Proxy Integration:**
   - ProxyManager MUST be used for all HTTP requests
   - Recent fix added `rotate_proxy()` method (was missing, caused crashes)
   - Health check available via `health_check()` method
   - **Apply to 2.5:** Use ProxyManager for all article fetching

3. **Error Handling:**
   - Code review found silent exception swallowing
   - Fixed to use proper logging and error propagation
   - **Apply to 2.5:** Log all extraction failures, don't swallow exceptions

4. **Testing Strategy:**
   - Unit tests for each extractor (mock HTTP responses)
   - Integration tests with real URLs (in `scripts/`)
   - Mock tests for Vision API integration
   - **Apply to 2.5:** Same pattern - unit tests + integration script

5. **LangGraph Migration:**
   - All processors migrated to StateGraph pattern
   - Each node exports `create_[name]_graph()` function
   - Workers call `.invoke(state)` instead of direct class methods
   - **Apply to 2.5:** Follow same StateGraph pattern for article_processor

6. **Worker Pattern:**
   - Separate worker file per content type (image_worker.py, video_worker.py)
   - Poll jobs table for `content_type='image'` and `status='pending'`
   - Update job status through processing pipeline
   - **Apply to 2.5:** Create article_worker.py for `content_type='link'` (non-social)

7. **Code Review Findings (Feb 9, 2026):**
   - ProxyManager missing methods caused runtime crashes
   - Extractors didn't use proxy (AC compliance issue)
   - Need comprehensive unit tests for all extractors
   - **Prevent in 2.5:** Ensure ProxyManager integration from start, write tests early

### Git Intelligence Summary

**Recent Commits (Last 10):**
- `07a7715`: Fix Story 2.4 code review issues (ProxyManager, tests)
- `27ada3a`: Persist video analysis to DB tables
- `8a1ae72`: Fix Twilio sender format in workers
- `056f462`: Introduce scraper worker + Twilio integration
- `b10c39e`: Implement Story 2.3 Video Frame Extraction
- `0698f0a`: Implement DLQ, Scraper & Vision tools with DB migrations

**Patterns Observed:**
1. **Database Persistence:** Recent work focuses on persisting results to `link_metadata` and `user_saved_links` tables
2. **Worker Architecture:** Multiple workers (classifier, video, image, scraper) all follow similar polling pattern
3. **Twilio Integration:** Workers send notifications back to users via Twilio
4. **Testing:** Integration tests in `scripts/` directory for real-world validation

**Apply to Story 2.5:**
- Follow same DB persistence pattern (save to `link_metadata` table)
- Create article_worker.py following established worker pattern
- Add Twilio notification on completion
- Create integration test script in `scripts/`

### Critical Developer Guardrails

**🚨 MUST DO:**
1. **Use Trafilatura as Primary:** It has the best precision/recall balance (2026 benchmarks)
2. **Implement Fallback Chain:** Trafilatura → Newspaper4k → BeautifulSoup (graceful degradation)
3. **Proxy All Requests:** Use ProxyManager for ALL HTTP requests (learned from Story 2.4 code review)
4. **Extract OpenGraph Tags:** Required for AC #5, use BeautifulSoup to parse `<meta property="og:*">`
5. **Classify Content Type:** Implement classifier for article/blog/documentation/generic (AC #8)
6. **Handle Paywalls Gracefully:** Detect and mark as `partial: true`, don't fail silently (AC #7)
7. **Return Full Text:** Store complete article text for downstream summarization (AC #6, Story 2.7 dependency)
8. **Follow LangGraph Pattern:** Use StateGraph for article_processor (consistency with 2.4)
9. **Write Tests Early:** Unit tests + integration script (prevent code review issues)
10. **Persist to DB:** Save results to `link_metadata` and `user_saved_links` tables (follow recent pattern)

**🚫 MUST NOT DO:**
1. **Don't Use newspaper3k:** It's unmaintained (stalled 2020), use newspaper4k instead
2. **Don't Skip Proxy:** All HTTP requests MUST go through ProxyManager (AC compliance)
3. **Don't Swallow Exceptions:** Log all errors properly (learned from Story 2.4 review)
4. **Don't Ignore OpenGraph:** Even if article extraction works, OG tags are required (AC #5)
5. **Don't Assume Static HTML:** Some sites may have dynamic content, handle gracefully

### Database Schema Notes

**Tables to Update:**
- `link_metadata`: Store article text, metadata, og_tags
- `user_saved_links`: Link user to saved article
- `jobs`: Update status from `pending` → `processing` → `complete`

**Expected Columns (from architecture):**
- `link_metadata.content_type`: Set to 'article', 'blog', 'documentation', or 'generic'
- `link_metadata.metadata_json`: Store extracted metadata (author, publish_date, site_name)
- `link_metadata.summary`: Full article text for downstream summarization

### Testing Requirements

### Unit Tests:
- `agent/tests/test_article_extractor.py`: Test Trafilatura extractor with mocked HTML
- `agent/tests/test_article_classifier.py`: Test content type classification
- `agent/tests/test_article_service.py`: Test unified service flow

**Integration Tests:**
- `scripts/test_article_extraction_integration.py`: Test with real URLs
  - News article (e.g., NYTimes, BBC)
  - Blog post (e.g., Medium, personal blog)
  - Documentation (e.g., Python docs, ReadTheDocs)
  - Generic page (e.g., Wikipedia)

**Test Execution:**
```bash
# Unit tests
python3 -m unittest agent/tests/test_article_*.py

# Integration test
python3 scripts/test_article_extraction_integration.py
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

- Dependency installation required `python3 -m pip install ... --break-system-packages` due to managed environment.
- Verified extraction on BBC, Simon Willison's blog, Python Docs, and Wikipedia.

### Completion Notes List

- Implemented `ArticleWorker` adhering to the new worker pattern.
- Integrated `Trafilatura` as primary extractor and `Newspaper4k` as fallback.
- Added OpenGraph parsing for rich metadata specific to articles.
- Implemented `ContentClassifier` to distinguish between articles, blogs, and documentation.
- Validated with both unit tests and live integration tests.

### File List

**Core Implementation:**
- `agent/requirements.txt` (MODIFIED - added trafilatura, newspaper4k)
- `agent/src/article_worker.py` (NEW)
- `agent/src/nodes/article_processor.py` (NEW)
- `agent/src/tools/article/classifier.py` (NEW)
- `agent/src/tools/article/service.py` (NEW)
- `agent/src/tools/article/types.py` (NEW)
- `agent/src/tools/article/extractors/base.py` (NEW)
- `agent/src/tools/article/extractors/newspaper_extractor.py` (NEW)
- `agent/src/tools/article/extractors/opengraph_parser.py` (NEW)
- `agent/src/tools/article/extractors/trafilatura_extractor.py` (NEW)

**Tests:**
- `agent/tests/test_article_classifier.py` (NEW)
- `agent/tests/test_article_extractor.py` (NEW)
- `agent/tests/test_article_service.py` (NEW)
- `scripts/test_article_extraction_integration.py` (NEW)
- `scripts/trigger_article_job.py` (NEW - manual test trigger)

**Deployment:**
- `agent/Dockerfile.article` (NEW)
- `agent/deploy-article.sh` (NEW)
- `agent/deploy-scraper.sh` (NEW)
- `agent/deploy-gcp.sh` (MODIFIED - updated for article worker)
- `cloudbuild-article.yaml` (NEW)

**Job Routing Fix (Code Review):**
- `agent/src/scraper_worker.py` (MODIFIED - added platform filter)
- `supabase/migrations/20260209000000_add_platform_to_jobs.sql` (NEW)

**Tracking:**
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (MODIFIED)
- `_bmad-output/implementation-artifacts/2-5-text-article-parser.md` (NEW - this file)
