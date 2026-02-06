---
stepsCompleted: []
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Video and Image Metadata Extraction for WhatsApp Content'
research_goals: 'Validate feasibility of extracting location, price, and vibe metadata from Instagram Reels and TikToks shared via WhatsApp.'
user_name: 'Pavan'
date: '2026-01-30'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-01-30
**Author:** Pavan
**Research Type:** technical

---

## Research Overview

This research focuses on the technical feasibility of the "Metadata Gap" identified in the brainstorming session. The core objective is to determine if existing AI and API technologies can reliability extract structured data (Location, Price, Vibe) from unstructured rich media (video/images) shared in a messaging context.

---


## Technology Stack Analysis

### Programming Languages

*   **Python:** The undisputed leader for this stack due to its dominance in AI/ML (LangChain, PyTorch) and rich ecosystem for web scraping (Playwright, Beautiful Soup).
    *   *Why:* Seamless integration with LangGraph and vector databases.
*   **TypeScript (Node.js):** Strong secondary contender for the high-concurrency webhook handling required by WhatsApp.
    *   *Role:* Potential use for the lightweight "Ingestion Service" (Twilio Webhook Handler) before offloading heavy processing to Python.

### AI & Machine Learning Stack

*   **Video Understanding:**
    *   **Twelve Labs:** Specialized "Video-to-Text" API that allows natural language querying of video content (e.g., "Find the scene with the menu price"). High accuracy but higher cost.
    *   **Google Cloud Video Intelligence:** robust for label detection ("Eiffel Tower", "Coffee") and text detection (OCR). Good balance of cost and reliability.
    *   **OpenAI GPT-4o:** Multimodal capabilities allow sending video frames directly for analysis. "Jack of all trades" for summary generation.
*   **Transcription:**
    *   **OpenAI Whisper:** Industry standard for reliable speech-to-text to capture verbally mentioned prices ("It's only $200!").

### Data Ingestion & Scraping

*   **Official API (Instagram Graph API):**
    *   *Status:* **Restrictive.** Rate limits (4800 calls/day variable) and strict token requirements make it risky for a high-volume consumer app.
    *   *Use Case:* Fetching metadata for *owned* accounts, but difficult for *competitor/public* content without business discovery limits.
*   **Grey-Hat Scrapers (Bright Data / ScrapFly):**
    *   *Status:* **Essential.** Necessary to reliably fetch the actual `.mp4` video URL from a public Instagram link without login friction.
    *   *Role:* The "Browser in the Cloud" that visits the link, handles the "Login to view" popup, and extracts the raw media URL for the AI to process.

### Database & Storage

*   **Vector Database (Pinecone / Chroma):**
    *   *Role:* Storing the "Semantic Index" of the content. Allows queries like "Cozy italian dinner" to find a reel that doesn't explicitly have those keywords in the text.
*   **Relational DB (PostgreSQL):**
    *   *Role:* User data, auth, saved trips, and structured metadata (Price: 200, Currency: USD).
*   **Redis:**
    *   *Role:* **Debouncing.** Buffer for "Burst Sharing" (user sends 10 links in 1 minute).

### Cloud Infrastructure

*   **Serverless (AWS Lambda / Google Cloud Functions):**
    *   *Fit:* specific "Extract Metadata" jobs are perfect for serverless. Spin up, process video, spin down.
*   **Orchestrator (LangGraph):**
    *   *Role:* Managing the state of the "Conversation". Knowing that *this* specific link belongs to the "Bali Trip" discussion thread.

### Technology Adoption Trends

*   **Shift to Multimodal:** The move from "Text NLP" to "Video Understanding" is the cutting edge of 2025. Standard OCR is no longer enough; "Visual Q&A" models are the new standard for content indexing.

## Integration Patterns Analysis

### API Design Patterns & Ingestion

*   **Webhook-First Architecture (Event-Driven):**
    *   **Pattern:** WhatsApp Business API pushes messages via Webhooks to a lightweight "Ingestion Service".
    *   **Verification:** reliability relies on validating `X-Hub-Signature-256` headers using the App Secret to prevent spoofing.
    *   **Response Standard:** The Ingestion Service must acknowledge receipt (`200 OK`) within **3 seconds**, or WhatsApp considers delivery failed. This mandates an asynchronous architecture.

### Communication Protocols

*   **Internal Service Communication:**
    *   **Redis Pub/Sub (Asynchronous):** The Ingestion Service pushes the raw payload to a Redis queue ("processing_queue"). This decouples the high-speed message intake from the slow-speed AI processing.
    *   **HTTPS/REST:** Used for the "Processing Worker" to call external APIs (OpenAI, Twelve Labs, ScrapFly).
    *   **HTTPS/REST:** Standard protocol for all internal services to keep the MVP stack simple and debuggable.

### System Interoperability (The "Async Worker" Pattern)

*   **The Orchestrator:** LangGraph acts as the state machine.
    *   **State Persistence:** Uses `PostgresSaver` with a `thread_id` (mapping to the user's phone number). This allows the bot to "remember" context across multiple messages.
    *   **Human-in-the-Loop:** LangGraph's "interrupt" pattern allows the bot to ask for clarification ("Is this a generic 'Stock' update or a specific 'Sale'?") and wait for a user reply before resuming the workflow.

### Microservices Integration

*   **Service Segmentation:**
    *   **Ingestion Service (Node.js/FastAPI):** Stateless, dumb, fast. Sole job: Verify signature, push to Redis, return 200 OK.
    *   **Brain Service (Python/LangGraph):** Stateful, smart, slow. Polls Redis, runs the AI pipeline, updates the DB, and sends the final answer back to the user asynchronously.

### Security Patterns

*   **Secret Management:**
    *   **Environment Variables:** Strictly storing `OPENAI_API_KEY`, `META_APP_SECRET`, etc., in environment variables, never in code.
*   **Webhook Security:**
    *   **HMAC Validation:** Determining message authenticity before processing.
*   **Token Management:**
    
## Architectural Patterns and Design

### System Architecture Patterns

*   **Agile Monolith-First (MVP Strategy):**
    *   *Decision:* Instead of complex microservices, we will start with a modular monolith (Ingestion + Worker) sharing a single Supabase backend.
    *   *Why:* Reduces infrastructure complexity (no k8s, no service mesh) allowing for rapid iteration.
*   **Event-Driven Architecture (EDA):**
    *   *Core Pattern:* The system is reactive. It sleeps until a Webhook wakes it up.
    *   *Decoupling:* The "Webhook Receiver" is decoupled from the "AI Processor" via a queue. This prevents the AI latency from timing out the WhatsApp connection.

### Design Principles (The "Stateless Bot")

*   **Stateless Services:** The bot code itself holds no memory.
    *   *Implementation:* Context is fetched from Postgres (via LangGraph checkpointing) for every single message turn.
    *   *Benefit:* We can scale the worker layer horizontally (1 worker or 100 workers) without breaking conversation flow.

### Scalability Patterns

*   **Vertical Scaling (Database):** Supabase (Postgres) will handle the load for 99% of the startup phase.
*   **Horizontal Scaling (Workers):** The "AI Processor" is CPU/Network bound. We can scale this layer infinitely on serverless platforms (AWS Lambda / Google Cloud Run) triggered by the Queue depth.

### Data Architecture (The Pivot to Supabase)

*   **Decision:** **Replacing Pinecone with Supabase (pgvector).**
    *   *Rationale:* Simplicity and Cost.
        *   **Cost:** Supabase's fixed monthly pricing ($25/mo for Pro) is cheaper and more predictable than Pinecone's usage-based model for small-to-medium datasets.
        *   **Unified Querying:** We can perform "Hybrid Search" (Vector + Relational) in a single SQL query (e.g., "Find vectors near 'Paris' WHERE price < $200 AND user_id = '123'"). This is significantly harder with Pinecone.
*   **Data Partitioning:**
    *   **User Isolation:** Row Level Security (RLS) in Supabase effectively isolates every user's data at the database engine level, a critical security feature for a multi-tenant bot.

### Deployment Architecture

*   **Infrastructure as Code:**
    *   **Repo Structure:** A monorepo containing `backend/ingestion`, `backend/worker` and `supabase/migrations`.

### Architectural Decisions & Examples

#### 1. Database: Pinecone vs. Supabase (The Verdict)

**Verdict: Supabase (pgvector) wins for MVP.**

*   **Why?**
    *   **Atomic Transactions:** You can save the "Link Metadata" (Title, URL) and the "Vector Embedding" in a single transaction. If one fails, both fail. Pinecone requires two separate API calls to two different systems.
    *   **Cost:** Supabase is a fixed $25/mo. Pinecone (Serverless) charges per read/write, which is harder to predict.
    *   **Simplicity:** One dashboard to debug everything.

**Developer Experience Comparison (Python):**

**Option A: Pinecone (The "Disconnected" Way)**
Requires managing two IDs (Database ID and Vector ID) to keep them in sync.
```python
# 1. Save metadata to your DB
db_item = db.insert({"url": "...", "title": "Bali Villa"}).execute()

# 2. Save vector to Pinecone (Must manually link ID)
index.upsert(
    vectors=[{
        "id": db_item.id,  # <--- CRITICAL: Must match DB ID
        "values": [0.1, 0.2, ...],
        "metadata": {"type": "vacation"}
    }]
)
# Risk: If step 2 fails, you have a "ghost" item in your DB with no search.
```

**Option B: Supabase vecs (The "Unified" Way)**
Using the `vecs` python library, it feels like a simple Python collection.
```python
import vecs

# Connect
db = vecs.create_client(DB_CONNECTION_STRING)
docs = db.get_or_create_collection(name="vacation_ideas", dimension=1536)

# Save everything in one go
docs.upsert(
    records=[
        (
            "vec1",           # ID
            [0.1, 0.2, ...],  # Vector
            {"url": "...", "title": "Bali Villa"} # Metadata
        )
    ]
)
# Result: Queryable via SQL *and* Vector Search immediately.
```

#### 2. WhatsApp Provider: Twilio vs. Meta Cloud API

**Verdict: Use Twilio for the MVP (First 4 weeks), then switch.**

*   **Why Twilio?**
    *   **Speed:** You can start testing in **5 minutes** using the Twilio Sandbox.
    *   **Verification Bubble:** Meta Cloud API requires "Business Verification" (uploading business license, waiting 3-5 days) before you can message more than 50 users. Twilio handles this complexity for you initially.
*   **Migration Plan:**
    *   Build the MVP with Twilio to get user feedback ASAP.
    *   Once you have traction, apply for Meta Business Verification and switch the backend to Meta Cloud API to save costs (Twilio adds a small markup).

#### 3. Protocol: gRPC vs. REST

**Verdict: Stick to REST for MVP.**
*   **Why:** gRPC is great for "Google Scale" (millions of ops/sec). For an MVP reacting to a few hundred messages a day, the complexity of setting up gRPC definitions (.proto files) is wasted effort. Standard HTTP/REST is perfectly fine and easier to debug.

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategies (The "Aggregator" Advantage)

*   **LLM Gateway (OpenRouter):**
    *   **Strategy:** We will use **OpenRouter** instead of direct provider APIs.
    *   **Benefit:** "Model Agility". We can swap `google/gemini-flash-1.5` (cheap/fast) for `anthropic/claude-3.5-sonnet` (smart/expensive) by changing *one string* in our config, without rewriting code. This is crucial for finding the cost/performance sweet spot for metadata extraction.
*   **Backend Validation:**
    *   **Phase 1 (Mock):** Hardcode the "Extraction" result to test WhatsApp UI flow.
    *   **Phase 2 (Single Model):** Use GPT-4o via OpenRouter to prove extraction works.
    *   **Phase 3 (Optimization):** A/B test cheaper models (Llama 3, Gemini) via OpenRouter to reduce costs.

### Development Workflows and Tooling

*   **Local Development:**
    *   **Supabase CLI:** Run `supabase start` to spin up a local Postgres + Vector + Auth emulator. No cloud latency during dev.
    *   **Tunneling:** Use **ngrok** to expose `localhost:8000` to Twilio/WhatsApp for webhook testing.
*   **Python Ecosystem:**
    *   **Dependency Management:** `poetry` for strict lockfiles (crucial when mixing LangChain, Pydantic, and Supabase libs).
    *   **Type Safety:** Strict `mypy` configuration to ensure our "Metadata Schema" is respected across the ingestion pipeline.

### Testing and Quality Assurance

*   **"Golden Set" Testing:**
    *   **Action:** Create a folder of 20 diverse Instagram Reels (Travel, Food, Fashion, Meme).
    *   **Pipeline:** Run the "Extraction Pipeline" against this set daily.
    *   **Automated Check:** "Did we extract 'Bali' from the Bali video?" (Regression testing).

### Deployment and Operations Practices

*   **Serverless Containers:**
    *   **Ingestion:** Deploy FastAPI to **Google Cloud Run** (scales to 0, costs $0 when idle).
    *   **Worker:** Deploy the LangGraph worker to the same Cloud Run service (or a separate one if scaling needs differ).
*   **Observability:**
    *   **Deep Tracing:** Use **LangSmith** (free tier) to trace every step of the AI chain (Input -> OpenRouter -> Output). This is the *only* way to debug "Why did the AI say that?".

### Cost Optimization

*   **The "Router" Savings:**
    *   OpenRouter allows us to route "easy" messages (e.g., "Hello") to cheap models ($0.10/M tokens) and "hard" messages (Video Analysis) to SOTA models ($5/M tokens).
*   **Supabase Free Tier:**
    *   Handles 500MB database and significant bandwidth, sufficient for the first 10,000 users.

## Technical Research Recommendations

### Implementation Roadmap

1.  **Day 1-2: The Plumbing.** Set up Twilio Sandbox -> FastAPI -> Redis -> Log to Console. Prove we can get a message.
2.  **Day 3-4: The Brain.** Connect FastAPI -> OpenRouter (GPT-4o). Send a text message "Paris Hotel", get a standard response back.
3.  **Day 5-7: The Eyes.** Integrate ScrapFly/BrightData to get the video URL. Pass frames to OpenRouter.
4.  **Day 8-10: Memory.** Implementation Supabase `vecs`. Store the result. Allow searching "Show me hotels".

### Technology Stack Recommendations (Final)

*   **Frontend:** WhatsApp (via Twilio).
*   **Backend:** Python (FastAPI).
*   **Database:** Supabase (Postgres + pgvector).
*   **LLM:** OpenRouter (routing to GPT-4o / Claude 3.5).
*   **Orchestration:** LangGraph.
*   **Infrastructure:** **Railway** (preferred for MVP) or Google Cloud Run.
    *   *Why Railway?* It offers "One Click Redis" (needed for our queue) and simpler deployment than GCP. For $5/mo, you avoid "Cold Start" timeouts that break WhatsApp.

### Success Metrics

*   **Extraction Accuracy:** >90% of locations correctly identified from Video.
*   **Latency:** <5 seconds for text, <30 seconds for video analysis.
*   **Cost:** <$0.02 per video processed.
