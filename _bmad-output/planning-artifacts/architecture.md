---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-01-31'
inputDocuments:
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/prd.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/product-brief-VaultBot-2026-01-30.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/research/technical-Video and Image Metadata Extraction for WhatsApp Content-research-2026-01-30.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/brainstorming/brainstorming-session-2026-01-30.md
workflowType: 'architecture'
project_name: 'VaultBot'
user_name: 'Pavan'
date: '2026-01-30'
---

# Architecture Decision Document

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
*   **Ingestion Pipeline:** Must handle multi-modal inputs (Text, Links, Images, Videos) via WhatsApp webhooks.
*   **Metadata Extraction:** Requires deep content analysis (OCR, Frame Extraction, Transcription) to convert raw media into structured data (`Location`, `Price`, `Vibe`).
*   **Semantic Search:** Enable natural language querying (`/search cozy cafe`) using vector similarity search.
*   **Card Generation:** Dynamic creation of OpenGraph images for visual feedback in chat.

**Non-Functional Requirements:**
*   **Latency:** Webhook acknowledgment < 2000ms (Twilio timeout limit).
*   **Reliability:** "Burst" handling for viral sharing moments; Dead Letter Queues for failed scrapes.
*   **Scalability:** Support for 100 concurrent requests (Future-proofing).
*   **Cost:** Minimize LLM/Vision tokens via Model Router (Small vs Large models).

**Scale & Complexity:**
*   **Primary Domain:** Async Backend API & Data Pipeline.
*   **Complexity Level:** Medium (High integration complexity, Low state complexity).
*   **Estimated Components:** 5-7 (API Gateway, Job Queue, Worker(s), Vector DB, Proxy Manager, Card Service).

### Technical Constraints & Dependencies
*   **WhatsApp/Twilio API:** Strict 24-hour customer service window constraints (less relevant for bots, but session management matters).
*   **LLM Latency:** Vision models are slow; architecture must be non-blocking.
*   **Proxy Dependence:** Scrapers rely on rotating residential proxies to avoid blocks.

### Cross-Cutting Concerns Identified
*   **Observability:** Tracing a request from "Webhook" -> "Queue" -> "Worker" -> "DB" is critical for debugging "Silent Failures".
*   **Rate Limiting:** Protecting the scraping infrastructure and LLM budget from abuse.
*   **Security:** Validating `X-Twilio-Signature` on every request.

## Starter Template Evaluation

### Primary Technology Domain
**Event-Driven Worker System** (Hybrid: Serverless Ingestion + Polling Workers).

### Selected Architecture: The "Async Brain" Pattern

**Structure:**
1.  **The Body (Ingestion):** Supabase Edge Functions (Deno/TypeScript).
2.  **The Brain (Processing)::** Cloud Run Jobs (Python Polling Workers).

**Rationale for Selection:**
*   **Simplicity Over Complexity:** Polling-based workers provide straightforward, debuggable processing vs stateful agent frameworks
*   **Timeout Avoidance:** Video processing takes >60s. Edge Functions would time out. Cloud Run Jobs support long-running processes.
*   **Independent Scaling:** Each worker type (classifier, scraper, video, image, article) scales independently based on workload
*   **Database as Queue:** Leverages Postgres as both data store and job queue, eliminating need for separate message broker

**Actual Implementation:**

**1. The Ingestion Layer (Supabase):**
```bash
supabase functions new webhook-handler
```
*   **Role:** Receive Webhook → Validate Signature → **(New) Privacy Check** → Push Job to Queue.
*   **Privacy Gate:** If `is_group` AND `!is_tagged`, return `200 OK` (Ignore). Do not queue.
*   **Deployment:** `supabase functions deploy webhook-handler`

**2. The Processing Layer (Cloud Run Workers):**
```bash
# Deploy 5 specialized workers
gcloud run jobs create vaultbot-classifier-worker --source=agent/ --region=us-central1
gcloud run jobs create vaultbot-scraper-worker --source=agent/ --region=us-central1
gcloud run jobs create vaultbot-video-worker --source=agent/ --region=us-central1
gcloud run jobs create vaultbot-image-worker --source=agent/ --region=us-central1
gcloud run jobs create vaultbot-article-worker --source=agent/ --region=us-central1
```

**Worker Responsibilities:**
*   **Classifier Worker (`worker.py`):** Polls for `status='pending' AND content_type IS NULL` → Classifies as link/video/image/text → Updates content_type
*   **Scraper Worker (`scraper_worker.py`):** Polls for `content_type='link'` → Scrapes metadata → Saves to link_metadata + user_saved_links
*   **Video Worker (`video_worker.py`):** Polls for `content_type='video'` → Extracts frames → Analyzes via Vision API
*   **Image Worker (`image_worker.py`):** Polls for `content_type='image'` → Analyzes via Vision API
*   **Article Worker (`article_worker.py`):** Polls for `content_type='article'` → Extracts text → Parses metadata
*   **Shared Services:**
    *   **Data Normalizer (`agent/src/tools/normalizer`):** Standardizes metadata into `Category`, `Price`, and `Tags` using LLM. Used by all workers.

**Polling Pattern:**
```python
while not shutdown_requested:
    job = fetch_and_lock_job()  # SELECT ... WHERE status='pending' AND content_type='X' LIMIT 1
    if job:
        process_job(job)  # UPDATE status='processing', do work, UPDATE status='complete'
    else:
        time.sleep(5)  # No jobs available
```

**Architectural Decisions:**

**Language & Runtime:**
*   **Ingestion:** TypeScript (Deno) - Runs on Supabase Edge
*   **Workers:** Python 3.9+ - Deployed as Cloud Run Jobs

**State Management:**
*   **Job Queue:** Postgres `jobs` table with atomic status updates
*   **Metadata Store:** Postgres `link_metadata`, `user_saved_links` tables
*   **User State:** Postgres `users` table

**Deployment:**
*   **Ingestion:** `supabase functions deploy` (Global Edge via Deno Deploy)
*   **Workers:** Cloud Run Jobs with Dockerfiles per worker type
*   **Database:** Supabase Postgres with pgvector extension

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
*   **Polling Workers:** Cloud Run Jobs polling Postgres queue (Deployed & Running)
*   **Vector Database:** Supabase `pgvector` enabled (Ready for Epic 3)
*   **Queue System:** Postgres `jobs` table with atomic claiming via RPC
*   **Authentication:** Twilio Signature Validation (Implemented in Edge Function)

**Important Decisions (Shape Architecture):**
*   **Extraction Strategy:** Dual-mode YouTube extraction (API primary, yt-dlp fallback)
*   **Deduplication:** `url_hash` based deduplication in `link_metadata` table
*   **Embeddings Model:** `text-embedding-3-small` (Planned for Epic 3)

**Deferred Decisions (Post-MVP):**
*   **Web Dashboard UI:** No React frontend initially
*   **User Login System:** Phone-number based identity only for MVP
*   **Group Membership Tracking:** Deferred to Epic 4

### Data Architecture

**Database Choice:** Supabase (PostgreSQL 16+)
*   **Rationale:** Unified Relational + Vector store. Simplifies future "Hybrid Search"
*   **Vector Extension:** `pgvector` enabled, HNSW indexing planned for Epic 3
*   **Connection Pooling:** Supabase default pooler (pgBouncer)

**Database Schema (Implemented):**

#### Core Tables

**1. `users` Table**
```sql
CREATE TABLE users (
  phone_number TEXT PRIMARY KEY,        -- WhatsApp phone number (e.g., '+15551234567')
  first_name TEXT,                      -- From ProfileName in webhook
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
*Purpose:* Auto-created user profiles (Story 1.4)

**2. `jobs` Table** (Job Queue)
```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT REFERENCES users(phone_number),
  user_phone TEXT NOT NULL,             -- Denormalized for quick access
  source_channel_id TEXT,               -- Group ID or user phone (for DMs)
  source_type TEXT CHECK(source_type IN ('dm', 'group')),
  content_type TEXT CHECK(content_type IN ('link', 'video', 'image', 'article', 'text')),
  platform TEXT,                        -- 'youtube', 'instagram', 'tiktok', 'generic'
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'complete', 'failed')),
  payload JSONB NOT NULL,               -- Original webhook payload
  result JSONB,                         -- Processing results
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX jobs_status_content_type_idx ON jobs(status, content_type);
CREATE INDEX jobs_user_phone_idx ON jobs(user_phone);
```
*Purpose:* Job queue with atomic claiming (Story 1.2)

**3. `link_metadata` Table** (Deduplication Layer)
```sql
CREATE TABLE link_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL,
  url_hash TEXT UNIQUE NOT NULL,        -- SHA-256 hash for deduplication
  platform TEXT NOT NULL,                -- 'youtube', 'instagram', 'tiktok'
  content_type TEXT NOT NULL,            -- 'link', 'image', 'video'
  extraction_strategy TEXT NOT NULL CHECK(extraction_strategy IN ('ytdlp', 'opengraph', 'api', 'vision')),
  title TEXT,
  description TEXT,
  author TEXT,
  thumbnail_url TEXT,
  duration INTEGER,                      -- Video duration in seconds
  scrape_status TEXT DEFAULT 'scraped',
  scrape_count INTEGER DEFAULT 1,        -- How many users saved this URL
  ai_summary TEXT,                       -- Epic 2 Story 2.7 (planned)
  normalized_category TEXT,              -- Epic 2 Story 2.6 (implemented)
  normalized_price_range TEXT,           -- Epic 2 Story 2.6 (implemented)
  normalized_tags TEXT[],                -- Epic 2 Story 2.6 (implemented)
  embedding VECTOR(1536),                -- Epic 3 Story 3.1 (planned)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX link_metadata_url_hash_idx ON link_metadata(url_hash);
CREATE INDEX link_metadata_platform_idx ON link_metadata(platform);
```
*Purpose:* Shared metadata store with deduplication (Story 2.2)

**4. `user_saved_links` Table** (User Attribution Layer)
```sql
CREATE TABLE user_saved_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  link_id UUID REFERENCES link_metadata(id),
  user_id TEXT REFERENCES users(phone_number),
  source_channel_id TEXT NOT NULL,      -- Group ID or user phone
  source_type TEXT NOT NULL CHECK(source_type IN ('dm', 'group')),
  attributed_user_id TEXT REFERENCES users(phone_number), -- Who shared it
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(link_id, user_id, source_channel_id)  -- Prevent duplicate saves
);

-- RLS Policy (Epic 4)
-- users can see their own saves OR group saves they're a member of
CREATE INDEX user_saved_links_user_idx ON user_saved_links(user_id);
CREATE INDEX user_saved_links_channel_idx ON user_saved_links(source_channel_id);
```
*Purpose:* Privacy-aware user tracking with attribution (Epic 4)

**5. `dlq_jobs` Table** (Dead Letter Queue)
```sql
CREATE TABLE dlq_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  original_job_id UUID,
  payload JSONB NOT NULL,
  error_message TEXT,
  error_details JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
*Purpose:* Failed job debugging (Story 1.5)

#### Database Functions

**`claim_pending_job()` RPC Function:**
```sql
CREATE OR REPLACE FUNCTION claim_pending_job()
RETURNS SETOF jobs AS $$
  UPDATE jobs
  SET status = 'processing', updated_at = NOW()
  WHERE id = (
    SELECT id FROM jobs
    WHERE status = 'pending'
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
  )
  RETURNING *;
$$ LANGUAGE SQL;
```
*Purpose:* Atomic job claiming prevents race conditions

**Schema Extensions (Privacy & Groups - Epic 4):**
*   **Jobs/Items:** `source_channel_id` and `source_type` support group vs DM context
*   **Attribution:** `attributed_user_id` tracks who shared content in groups
*   **RLS Policy (Planned):** `user_id = me OR source_channel_id IN my_groups`


### Authentication & Security

**Ingestion Security:** Twilio Signature Validation
*   **Mechanism:** Middleware validates `X-Twilio-Signature` header using HMAC-SHA1 and Auth Token.
*   **Action:** 403 Forbidden for any mismatch.

**Internal Security:** Row Level Security (RLS)
*   **Pattern:** Even the "System Bot" operates nicely with RLS. The Worker Service uses a `SERVICE_ROLE_KEY` but respects user isolation policies where possible.

### API & Communication Patterns

**Internal Protocol:** Asynchronous Job Queue
*   **Flow:** Webhook -> `SUPABASE_EDGE` -> `INSERT INTO queue_table` -> `LANGGRAPH_POLLER` -> `PROCESS`.
*   **Rationale:** Decouples the 2-second Twilio timeline from the 60-second AI timeline.
*   **Search Scope:** API queries must pass context: `scope: 'global' | 'group'` to determine RLS filter.

### Infrastructure & Deployment

**Ingestion:** Supabase Edge Functions
*   **Deploy:** `supabase functions deploy`.
*   **Scale:** Serverless auto-scale.

**Processing:** LangGraph Cloud (or Cloud Run)
*   **Deploy:** Dockerized Python Agent.
*   **Scale:** Horizontal worker scaling based on queue depth.
*   **Messaging:** Abstracted via `MessagingProvider` interface to decouple from Twilio SDK. `TwilioMessagingService` is the concrete implementation.

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Database Naming Conventions:**
*   **Standard:** `snake_case` (Postgres Standard).
*   **Tables:** Plural (e.g., `users`, `items`, `jobs`).
*   **Foreign Keys:** Singular + `_id` (e.g., `user_id`).
*   **Vectors:** `embedding` (standard vector column name).

**API & Code Naming Conventions:**
*   **Hybrid Rule:**
    *   **Python (Agent):** Strict `snake_case` for everything.
    *   **TypeScript (Ingestion):** `camelCase` for internal logic, BUT...
    *   **Interface Rule:** Types that mirror DB tables OR Queue Payloads MUST use `snake_case` keys to match the wire format.
    *   *Bad:* `interface Job { userId: string }`
    *   *Good:* `interface Job { user_id: string }`

### Structure Patterns

**Actual Monorepo Structure:**
*   `/supabase`: All Supabase config (Migrations, Edge Functions)
*   `/agent`: Python Worker Applications (5 specialized workers)
*   `/docs`: Project documentation
*   `/scripts`: Testing and utility scripts
*   `/_bmad-output`: BMAD planning and implementation artifacts

### Communication Patterns

**Polling-Based Job Queue:**
*   **Table:** `jobs`
*   **Key Columns:** 
    - `id` (UUID, PK)
    - `status` (ENUM: 'pending', 'processing', 'complete', 'failed')
    - `content_type` (ENUM: 'link', 'video', 'image', 'article', 'text')
    - `platform` (VARCHAR: 'youtube', 'instagram', 'tiktok', 'generic', etc.)
    - `payload` (JSONB: original webhook data)
    - `result` (JSONB: processing results)
*   **Atomic Claiming:** Workers use `claim_pending_job()` RPC function for race-condition-free job claiming
*   **Status Flow:** `pending` → `processing` → `complete` or `failed`

**Example Payload:**
```json
{
  "From": "whatsapp:+15551234567",
  "Body": "https://youtube.com/watch?v=...",
  "MessageSid": "SM...",
  "ProfileName": "John Doe"
}
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
VaultBot/
├── supabase/                       # [The Body] - TypeScript (Ingestion)
│   ├── functions/
│   │   ├── webhook-handler/        # Twilio webhook → Privacy gate → Job queue
│   │   └── _shared/                # Shared types
│   ├── migrations/                 # Database schema evolution
│   │   ├── 20260129000000_create_users_table.sql
│   │   ├── 20260129000001_create_jobs_table.sql
│   │   ├── 20260206000002_enable_pgvector.sql
│   │   ├── 20260207000000_create_link_metadata_table.sql
│   │   └── 20260207000001_create_user_saved_links_table.sql
│   └── config.toml
├── agent/                          # [The Brain] - Python (Workers)
│   ├── src/
│   │   ├── worker.py               # Classifier Worker (entry point)
│   │   ├── scraper_worker.py       # Scraper Worker (entry point)
│   │   ├── video_worker.py         # Video Worker (entry point)
│   │   ├── image_worker.py         # Image Worker (entry point)
│   │   ├── article_worker.py       # Article Worker (entry point)
│   │   ├── nodes/                  # Processing logic
│   │   │   └── classifier.py       # Content type classification
│   │   ├── interfaces/             # Abstract Interfaces (Messaging, etc.)
│   │   ├── infrastructure/         # Concrete Implementations (TwilioAdapter)
│   │   ├── tools/                  # Reusable capabilities
│   │   │   ├── scraper/            # Link scraping (yt-dlp, OpenGraph)
│   │   │   └── vision/             # Vision API integration
│   │   └── prompts/                # LLM prompt templates
│   ├── tests/                      # Unit & integration tests
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile.classifier       # Classifier worker container
│   ├── Dockerfile.scraper          # Scraper worker container
│   ├── Dockerfile.video            # Video worker container
│   ├── Dockerfile.image            # Image worker container
│   ├── Dockerfile.article          # Article worker container
│   ├── deploy-gcp.sh               # Main deployment script
│   └── DEPLOYMENT.md               # Deployment guide
├── scripts/                        # Testing & utilities
│   └── test_scraper_live.py
├── docs/                           # Project documentation
└── _bmad-output/                   # Planning artifacts
    ├── planning-artifacts/
    │   ├── prd.md
    │   ├── architecture.md
    │   └── epics.md
    └── implementation-artifacts/
        └── sprint-status.yaml
```

### Architectural Boundaries

**API Boundaries:**
*   **External (Ingestion):** `POST /functions/v1/webhook-handler` (Public, Twilio-Secured)
*   **Internal (Agent):** `SELECT * FROM jobs` (Polled by Agent via DB Connection).

**Component Boundaries:**
*   **Ingestion Service (Supabase):** "Dumb Pipe". Knows nothing about AI or Vectors. Only validates Twilio security and formats the Job JSON.
*   **Reasoning Service (Agent):** "Smart Consumer". Knows nothing about HTTP Webhooks. Consumes Jobs, executes logic, writes back to DB.

**Data Boundaries:**
*   **Shared Schema:** Both services share the SAME Database.
    *   *Ingestion* has `INSERT` permission on `jobs`.
    *   *Agent* has `SELECT/UPDATE` on `jobs` and `INSERT` on `items/vectors`.

### Requirements to Structure Mapping

**Epic: Ingestion Pipeline**
*   **Live in:** `supabase/functions/webhook-handler/`
*   **Schema:** `supabase/migrations/20260130_create_jobs_table.sql`

**Epic: Metadata Extraction**
*   **Live in:** `agent/src/nodes/extractor.py`
*   **Tools:** `agent/src/tools/vision_api.py`

**Epic: Semantic Search**
*   **Live in:** `agent/src/tools/vector_search.py`
*   **Schema:** `supabase/migrations/20260130_enable_pgvector.sql`

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
*   The "Hybrid" approach (Supabase for Ingestion + LangGraph for Reasoning) successfully resolves the conflict between Twilio's strict 2-second timeout and the long-running nature of Video extraction.
*   The use of a shared Postgres database for both "Hot" state (LangGraph Checkpoints) and "Cold" data (Users, Items) minimizes infrastructure complexity.

**Pattern Consistency:**
*   The `snake_case` data contract effectively mitigates the friction between TypeScript (Ingestion) and Python (Agent), ensuring a consistent Schema-First approach.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
*   **Ingestion:** Fully covered by the `supabase/functions/webhook-handler`.
*   **Metadata Extraction:** Addressed by the LangGraph `extractor` node and `vision_api` tool.
*   **Semantic Search:** Enabled by `pgvector` and the `vector_search` tool.
*   **Zero-UI:** Supported by the Card Generation logic returning images to the chat.

**Non-Functional Requirements Coverage:**
*   **Latency:** Handled by the async queue architecture (immediate ack, async process).
*   **Scalability:** Serverless functions and containerized agents scale horizontally.

### Implementation Readiness Validation ✅

**Structure Completeness:**
*   The project structure clearly separates the "Body" (Supabase) from the "Brain" (Agent), with clear boundaries and integration points via the Database.

**Gap Analysis Results:**
*   **Gap:** Local development experience for the "Hybrid" stack (running Deno + Python simultaneously) needs good documentation.
*   **Gap:** Monitoring/Observability across the Queue boundary requires careful setup (e.g., correlating a Twilio Request ID with a LangGraph Run ID).

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
*   **Resilience:** The Async Queue pattern protects the system from "Burst" traffic and Twilio timeouts.
*   **Maintainability:** Clear separation of concerns between "Dumb" Ingestion and "Smart" Reasoning.

### Implementation Handoff

**First Implementation Priority:**
Initialize the Supabase project and create the `jobs` table to establish the communication backbone.

```bash
supabase init
supabase start
```


