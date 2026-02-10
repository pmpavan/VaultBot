# Story 2.6: Data Normalizer Agent

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a System,
I want to standardize the chaotic AI output into a clean schema,
So that we can run SQL queries on `price` and `category`.

## Acceptance Criteria

1. **Given** a raw AI description (e.g., "It looks like a pricey sushi place, maybe 100 bucks")
2. **When** the Normalizer Agent runs
3. **Then** it MUST output a JSON object: `{ "category": "Food", "price_range": "$$$", "tags": ["Sushi", "Japanese", "Date Night"] }`
4. **And** It MUST strictly adhere to the defined ENUMs for Category
5. **And** Price ranges MUST be normalized to: `$` (budget), `$$` (moderate), `$$$` (expensive), `$$$$` (luxury), or `null` if not applicable
6. **And** Tags MUST be extracted as an array of semantic descriptors (e.g., cuisines, vibes, use cases)
7. **And** The normalized data MUST be persisted to `link_metadata` table columns: `normalized_category`, `normalized_price_range`, `normalized_tags`
8. **And** The normalizer MUST handle missing or ambiguous input gracefully (return null/empty values rather than hallucinating)

## Tasks / Subtasks

- [ ] **Design Category Taxonomy** (AC: 4)
  - [ ] Define comprehensive category ENUM (Food, Entertainment, Travel, Shopping, Education, Health, etc.)
  - [ ] Document category definitions and examples
  - [ ] Handle edge cases (e.g., hybrid content like "cooking tutorial video")

- [ ] **Create Normalizer Prompt** (AC: 1, 2, 3)
  - [ ] Design structured prompt requesting JSON output with category/price/tags
  - [ ] Include category taxonomy in prompt
  - [ ] Add examples for few-shot learning
  - [ ] Enforce strict JSON schema validation

- [ ] **Implement Normalizer Tool** (AC: 1-8)
  - [ ] Create `agent/src/tools/normalizer/` module
  - [ ] Implement `NormalizerService` that calls LLM with structured prompt
  - [ ] Parse and validate LLM response against schema
  - [ ] Handle LLM failures gracefully (retry logic, fallback to defaults)
  - [ ] Support batch normalization for efficiency

- [ ] **Integrate with Worker Pipeline** (AC: 7)
  - [ ] Update existing workers (scraper, video, image, article) to call normalizer
  - [ ] Normalizer should run AFTER metadata extraction but BEFORE final persistence
  - [ ] Update `link_metadata` table with normalized fields
  - [ ] Ensure idempotency (don't re-normalize if already normalized)

- [ ] **Testing** (AC: 1-8)
  - [ ] Unit tests for normalizer with various input descriptions
  - [ ] Test edge cases: ambiguous descriptions, missing context, multi-category content
  - [ ] Integration test with full worker pipeline
  - [ ] Validate database persistence

## Dev Notes

### Architecture Patterns & Constraints

**Core Design Pattern:**
- **LLM-Powered Structured Extraction:** Use OpenRouter (GPT-4o or Claude) to convert unstructured AI descriptions into structured JSON
- **Schema Enforcement:** Pydantic models to validate LLM output before database persistence
- **Fail-Safe Defaults:** If normalizer fails, don't block pipeline - save with null normalized fields

**Location:** `agent/src/tools/normalizer/`

**Database Integration:**
- **Target Table:** `link_metadata` (L27-L29 in architecture.md)
- **Columns:**
  - `normalized_category` (TEXT): Single category from predefined ENUM
  - `normalized_price_range` (TEXT): `$`, `$$`, `$$$`, `$$$$`, or NULL
  - `normalized_tags` (JSONB): Array of semantic tags

**LLM Integration:**
- **Model:** GPT-4o-mini or Claude-3.5-Haiku (fast, cheap, good at structured extraction)
- **Prompt Style:** Few-shot with strict JSON schema
- **Fallback:** If model fails or returns invalid JSON → log warning, continue with null values

**Worker Integration Pattern:**
All existing extraction workers (scraper, video, image, article) should call normalizer:
```
1. Extract raw metadata (title, description, AI summary)
2. Call Normalizer with combined context
3. Update link_metadata with normalized fields
4. Mark job as complete
```

### Project Structure Notes

**Recommended File Structure:**
```
agent/src/tools/normalizer/
├── __init__.py
├── types.py                # Pydantic models: NormalizerRequest, NormalizerResponse, CategoryEnum
├── service.py              # NormalizerService class
├── prompts.py              # Normalizer prompts (system + user)
└── taxonomy.py             # Category definitions and examples
```

**Database Schema (Already Exists):**
Migration `20260207000000_create_link_metadata_table.sql` already has placeholders:
```sql
normalized_category text,           -- Story 2.6: Data Normalizer
normalized_price_range text,        -- Story 2.6
normalized_tags jsonb,               -- Story 2.6: Array of tags
```

### Latest Technical Information

**LLM Structured Output (2026 Best Practices):**

1. **JSON Mode Enforcement:**
   - OpenRouter supports `response_format: { "type": "json_object" }` for GPT-4o
   - Claude uses prompt engineering: "Return ONLY valid JSON, no markdown"
   - **Error Rate:** JSON mode reduces hallucinated fields by ~80%

2. **Few-Shot Learning:**
   - Include 3-5 examples in system prompt showing input → output transformation
   - **Example:**
     ```
     Input: "Expensive Italian restaurant in Manhattan, reservations required"
     Output: {"category": "Food", "price_range": "$$$", "tags": ["Italian", "Fine Dining", "Manhattan"]}
     ```

3. **Schema Validation:**
   - Use Pydantic models to validate LLM response
   - **Pattern:** `NormalizerResponse.model_validate_json(llm_output)`
   - Catch `ValidationError` and retry or use fallback

4. **Model Selection:**
   - **GPT-4o-mini:** Faster, cheaper ($0.15/1M input tokens), excellent for structured tasks
   - **Claude-3.5-Haiku:** Even cheaper ($0.80/1M input tokens), good JSON adherence
   - **Decision:** Use GPT-4o-mini as primary (better JSON mode support)

### Category Taxonomy (Initial Proposal)

**Primary Categories:**
- `Food` - Restaurants, cafes, recipes, food content
- `Travel` - Destinations, hotels, travel guides, transportation
- `Entertainment` - Movies, music, events, nightlife, arts
- `Shopping` - Products, stores, e-commerce, deals
- `Education` - Courses, tutorials, learning resources, documentation
- `Health` - Fitness, wellness, medical information, mental health
- `Technology` - Gadgets, software, tech news, coding tutorials
- `Lifestyle` - Home decor, fashion, beauty, personal development
- `Business` - Entrepreneurship, marketing, finance, productivity
- `Sports` - Games, athletes, fitness activities, sports news
- `News` - Current events, politics, world news
- `Other` - Fallback for uncategorizable content

**Hybrid Handling:**
- If content spans multiple categories (e.g., "cooking tutorial" = Food + Education)
- **Primary category:** Food (the subject)
- **Tags:** Include "Tutorial", "Cooking", "Learning"

### References

- **Architecture:** [architecture.md#L199-L203](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md#L199-L203) (Database schema)
- **PRD:** [prd.md#L213](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/prd.md#L213) (FR-07: Data Normalization)
- **Epics:** [epics.md#L248-L260](file:///Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/epics.md#L248-L260) (Story 2.6 definition)
- **Database Migration:** [20260207000000_create_link_metadata_table.sql](file:///Users/apple/P1/Projects/Web/VaultBot/supabase/migrations/20260207000000_create_link_metadata_table.sql#L27-L29)
- **Existing Workers:** 
  - [scraper_worker.py](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/scraper_worker.py)
  - [video_worker.py](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/video_worker.py)
  - [image_worker.py](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/image_worker.py)
  - [article_worker.py](file:///Users/apple/P1/Projects/Web/VaultBot/agent/src/article_worker.py)

### Previous Story Intelligence

**Key Learnings from Previous Stories:**

1. **Structured Extraction Pattern (Story 2.1: Vision API):**
   - Use Pydantic models for request/response types
   - Prompts defined in `agent/src/prompts/` directory
   - System prompts inherit from `VaultBotJsonSystemPrompt` base class
   - **Apply to 2.6:** Follow same pattern for normalizer prompts

2. **Worker Integration (Stories 2.2-2.5):**
   - Each worker polls for specific `content_type` jobs
   - Workers follow pattern: fetch → process → persist → notify
   - Use `link_metadata` table for shared metadata (deduplication via `url_hash`)
   - **Apply to 2.6:** Normalizer should be called by ALL workers, not a separate worker

3. **Error Handling (From Code Reviews):**
   - Don't swallow exceptions silently
   - Log all failures with context
   - Continue pipeline even if normalizer fails (graceful degradation)
   - **Apply to 2.6:** Wrap normalizer in try/except, save with null values on failure

4. **Prompt Engineering (Story 2.1):**
   - System prompts use JSON format: `model_dump_json()`
   - Vision prompts define clear instructions + format expectations
   - **Apply to 2.6:** Create `NormalizerSystemPrompt` and `NormalizerUserPrompt` classes

5. **Database Persistence:**
   - Use Supabase client with RPC for atomic updates
   - Follow pattern: `supabase.table('link_metadata').update(...).eq('id', link_id).execute()`
   - **Apply to 2.6:** Workers will call normalizer and update existing `link_metadata` rows

### Git Intelligence Summary

**Recent Commits (Last 10):**
- `db26db3`: Disable proxy for Instagram (BrightData blocks it too)
- `7d7ec45`: Add YouTube Data API support (primary method)
- `bc1921c`: Fix YouTube scraping: disable proxy for YouTube
- `3a41ebe`: Fix Story 2.5 code review issues and improve migration idempotency
- `07a7715`: Fix Story 2.4 code review issues
- `27ada3a`: Persist video analysis to `link_metadata` and `user_saved_links` tables
- `8a1ae72`: Fix Twilio sender format in workers
- `056f462`: Introduce scraper worker and enhance Twilio integration

**Patterns Observed:**
1. **Metadata Persistence:** All workers now save to `link_metadata` table (Story 2.2-2.5)
2. **Worker Architecture:** 5 specialized workers deployed on Cloud Run
3. **Deduplication:** URL hashing prevents duplicate scraping
4. **Testing:** Integration scripts in `scripts/` for real-world validation

**Apply to Story 2.6:**
- Normalizer should integrate into existing metadata persistence flow
- Don't create a separate normalizer worker - call from existing workers
- Add integration test script: `scripts/test_normalizer_integration.py`

### Critical Developer Guardrails

**🚨 MUST DO:**

1. **Define Category Taxonomy First:** Create exhaustive ENUM of categories before writing code
2. **Use Few-Shot Prompts:** Include 5-10 examples in normalizer prompt for better accuracy
3. **Validate LLM Output:** Use Pydantic models to validate JSON structure before database save
4. **Handle Failures Gracefully:** If normalizer errors, log warning and continue with null values (don't block pipeline)
5. **Batch Processing:** If calling normalizer for multiple items, batch requests to reduce API calls
6. **Model Selection:** Use GPT-4o-mini (fast, cheap, good at structured extraction)
7. **Price Range Precision:** Strictly enforce `$`, `$$`, `$$$`, `$$$$`, or NULL - no other values
8. **Tag Quality:** Limit tags to 3-7 semantic descriptors (avoid generic tags like "content" or "video")
9. **Integration Point:** Call normalizer AFTER metadata extraction, BEFORE final persistence
10. **Idempotency:** Check if `normalized_category` already exists before re-normalizing

**🚫 MUST NOT DO:**

1. **Don't Create Separate Worker:** Normalizer should be a tool called BY existing workers, not standalone
2. **Don't Hallucinate Categories:** If content doesn't fit taxonomy, use "Other" - don't invent new categories
3. **Don't Block on Failure:** If LLM times out or returns invalid JSON, continue with null values
4. **Don't Over-Tag:** Keep tags focused and relevant (3-7 max) - avoid tag spam
5. **Don't Use Expensive Models:** GPT-4o-mini is sufficient - don't use full GPT-4o or Claude-3.5-Sonnet
6. **Don't Ignore Existing Data:** If `normalized_category` already populated, skip normalization (idempotency)
7. **Don't Forget Error Logging:** Log normalizer failures for debugging and taxonomy refinement

### Database Schema Notes

**Tables to Update:**
- `link_metadata`: Add normalized fields to existing rows (UPDATE operation)

**Expected Flow:**
1. Worker extracts metadata, creates `link_metadata` row with `title`, `description`, etc.
2. Worker calls normalizer with combined context
3. Worker UPDATES same `link_metadata` row with `normalized_category`, `normalized_price_range`, `normalized_tags`
4. Worker marks job as complete

**Schema Constraints:**
- `normalized_category` is TEXT (no ENUM constraint in DB - validation happens in code)
- `normalized_price_range` is TEXT (`$`, `$$`, `$$$`, `$$$$`, NULL)
- `normalized_tags` is JSONB (array of strings)

**Query Examples (Future Search Features):**
```sql
-- Find all expensive restaurants
SELECT * FROM link_metadata 
WHERE normalized_category = 'Food' 
AND normalized_price_range IN ('$$$', '$$$$');

-- Find all content with specific tags
SELECT * FROM link_metadata 
WHERE normalized_tags @> '["Italian", "Fine Dining"]'::jsonb;
```

### Testing Requirements

**Unit Tests:**
- `agent/tests/test_normalizer_service.py`:
  - Test category extraction from various descriptions
  - Test price range detection (explicit prices, ranges, qualitative terms)
  - Test tag extraction quality
  - Test edge cases: ambiguous input, empty descriptions, multi-category content
  - Test JSON validation and error handling

**Integration Tests:**
- `scripts/test_normalizer_integration.py`:
  - Test normalizer with real extracted metadata from YouTube, Instagram, articles
  - Test database UPDATE flow (create link_metadata, normalize, verify persistence)
  - Test worker integration (e.g., trigger scraper job, verify normalized fields saved)

**Test Examples:**
```python
# Unit test examples
test_cases = [
    {
        "input": "Expensive sushi restaurant in Tokyo, omakase style, $200 per person",
        "expected": {
            "category": "Food",
            "price_range": "$$$$",
            "tags": ["Sushi", "Japanese", "Omakase", "Tokyo", "Fine Dining"]
        }
    },
    {
        "input": "Budget travel tips for backpacking Europe",
        "expected": {
            "category": "Travel",
            "price_range": "$",
            "tags": ["Backpacking", "Europe", "Budget Travel", "Travel Tips"]
        }
    },
    {
        "input": "Python tutorial for beginners - free course",
        "expected": {
            "category": "Education",
            "price_range": None,
            "tags": ["Python", "Programming", "Tutorial", "Beginner", "Free"]
        }
    }
]
```

**Test Execution:**
```bash
# Unit tests
python3 -m unittest agent/tests/test_normalizer_service.py

# Integration test
python3 scripts/test_normalizer_integration.py
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
