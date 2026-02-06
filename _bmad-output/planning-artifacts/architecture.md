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
**Event-Driven Agentic System** (Hybrid: Serverless + Durable Agent).

### Selected Architecture: The "Async Brain" Pattern

**Structure:**
1.  **The Body (Ingestion):** Supabase Edge Functions (Deno).
2.  **The Brain (Processing):** LangGraph Cloud (Python/JS).

**Rationale for Selection:**
*   **Best of Both Worlds:** We get the "Zero Ops" simplicity of Supabase for the high-volume webhook intake, and the "Durable State" of LangGraph for the long-running video extraction agents.
*   **Timeout Avoidance:** Video processing takes >60s. Edge Functions would time out. LangGraph Cloud supports long-running jobs natively.
*   **Agentic Future-Proofing:** We start with extraction, but LangGraph allows us to add "Clarification Loops" (e.g., asking the user "Did you mean this place?") without rewriting the entire stack.

**Initialization Strategy:**

**1. The Ingestion Layer (Supabase):**
```bash
supabase functions new webhook-handler
```
*   **Role:** Receive Webhook -> Validate Signature -> **(New) Privacy Check** -> Push Job to Queue.
*   **Privacy Gate:** If `is_group` AND `!is_tagged`, return `200 OK` (Ignore). Do not queue.

**2. The Processing Layer (LangGraph):**
```bash
pip install langgraph langsmith
langgraph new vaultbot-agent
```
*   **Role:** Pull Job -> Extract Metadata -> Vectorize -> Save to DB -> Send Final WhatsApp Reply.

**Architectural Decisions Provided by Hybrid Stack:**

**Language & Runtime:**
*   **Ingestion:** TypeScript (Deno).
*   **Agent:** Python (Recommended for best AI library support).

**State Management:**
*   **Hot State:** LangGraph Checkpointer (Postgres) tracks the "Conversation" state.
*   **Cold State:** Supabase Database (Items, Users).

**Deployment:**
*   **Ingestion:** `supabase functions deploy` (Global Edge).
*   **Agent:** `langgraph deploy` (LangGraph Cloud) or Dockerized Cloud Run.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
*   **Hybrid Runtime:** Supabase Edge (Ingestion) + LangGraph (Processing).
*   **Vector Database:** Supabase `pgvector` (Unified capability).
*   **Queue System:** Postgres-based Queue (Simple handoff).
*   **Authentication:** Twilio Signature Validation (Mandatory security).

**Important Decisions (Shape Architecture):**
*   **Embeddings Model:** `text-embedding-3-small` (Cost/Perf balance).
*   **Agent framework:** LangGraph (Python) for durable execution.

**Deferred Decisions (Post-MVP):**
*   **Web Dashboard UI:** No React frontend initially.
*   **User Login System:** Phone-number based identity only for MVP.
*   **Privacy Control Store:** `fastKV` (Redis) for `/pause` state (Implemented if scale > 100 users).

### Data Architecture

**Database Choice:** Supabase (PostgreSQL 16+)
*   **Rationale:** Unified Relational + Vector store. Simplifies "Hybrid Search" (e.g., "Find jazz bars [vector] that are cheap [SQL]").
*   **Vector Extension:** `pgvector` with HNSW indexing for performance.
*   **State Store:** `langgraph-checkpoint-postgres` (Persists agent state in same DB).

**Schema Extensions (Privacy & Groups):**
*   **Jobs/Items:** Added `source_channel_id` (Group ID) and `source_type` ('dm' | 'group').
*   **Attribution:** Added `attributed_user_id` to Items (Who saved it?).
*   **Isolation Policy:** RLS must enforce `user_id = me OR source_channel_id IN my_groups`.

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

**Proposed Monorepo Structure:**
*   `/supabase`: All Supabase config (Migrations, Edge Functions).
*   `/agent`: The Python LangGraph Application (Graph, Nodes, Tools).
*   `/docs`: Documentation.
*   `bmad-config.yaml`: Agent definitions.

### Communication Patterns

**Event System (The Queue):**
*   **Table:** `jobs`
*   **Column:** `payload` (JSONB)
*   **Schema Standard:**
    ```json
    {
      "type": "video_processing",
      "user_phone": "+1555...",
      "source_channel": "group-123",
      "source_type": "group",
      "media_url": "https://..."
    }
    ```
*   **Rule:** Always include `user_phone` as the persistent identifier.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
vaultbot/
├── supabase/                  # [The Body] - TypeScript (Ingestion)
│   ├── functions/
│   │   ├── webhook-handler/   # FR: Handle Twilio Webhook -> Validate -> Queue
│   │   └── _shared/           # Shared Types (Queue Payloads)
│   ├── migrations/            # DB Schema (jobs, vectors, users)
│   └── config.toml            # Project Config
├── agent/                     # [The Brain] - Python (Processing)
│   ├── src/
│   │   ├── graph/             # LangGraph State Machine Definition
│   │   ├── nodes/             # Logic: Extract, Vectorize, Generate Card
│   │   └── tools/             # Capabilities: Database, Vision API
│   ├── tests/                 # Agent Logic Tests
│   ├── pyproject.toml         # Python Dependencies
│   └── Dockerfile             # Container Definition for Cloud Run
├── docs/                      # [The Memory] - Project Documentation
│   ├── architecture.md
│   ├── prd.md
│   └── ux-design-specification.md
└── bmad-config.yaml           # Agent Configuration
```

### Architectural Boundaries

**API Boundaries:**
*   **External (Ingestion):** `POST /functions/v1/webhook-handler` (Public, Twilio-Secured).
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


