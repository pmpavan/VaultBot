---
inputDocuments:
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/product-brief-VaultBot-2026-01-30.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/research/technical-Video and Image Metadata Extraction for WhatsApp Content-research-2026-01-30.md
  - /Users/apple/P1/Projects/Web/VaultBot/docs/The Architecture of Information Fragmentation_ A Technical and Market Evaluation of MicroSaaS Solutions for Messaging-Based Content Organization.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/brainstorming/brainstorming-session-2026-01-30.md
stepsCompleted: [step-01-init, step-02-discovery, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-e-01-discovery, step-e-02-review, step-e-03-edit]
workflowType: 'prd'
classification:
  projectType: api_backend
  domain: general
  complexity: medium
  projectContext: greenfield
lastEdited: '2026-01-31'
editHistory:
  - date: '2026-01-31'
    changes: 'Integrated explicit Group vs DM logic, privacy rules, and detailed user journeys for memory migration.'
---

# Product Requirements Document - VaultBot

**Author:** Pavan
**Date:** 2026-01-30

## Executive Summary

**Vision:** "The Memory Prosthetic". VaultBot becomes the backend API for personal knowledge management, passively ingesting content from any messaging platform and auto-populating the user's life operating system (Calendar, Maps, Todo) without manual intervention.

**Problem:** Users face "Information Fragmentation" and "Write-Only Memory". Valuable content shared in WhatsApp groups (Reels, Links, Locations) is buried in chat history and never retrieved.

**Solution:** A WhatsApp Bot that intercepts shared content, autonomously extracts semantic metadata (Location, Price, Vibe), and makes it searchable via natural language ("Show me that jazz bar Ananya shared").

## Success Criteria

### User Success
*   **Retrieval Rate (North Star):** The percentage of saved items that are subsequently "retrieved" (searched for, viewed, or clicked) within 30 days. Proves we are solving the "Write-Only Memory" problem.
*   **Interpretation Accuracy:** >90% rate at which the AI correctly identifies the "Core Subject" (e.g., "This is a restaurant" vs "This is a cat video") within rich media.
*   **Time-to-Value:** Users receive the "Stored Confirmation" with extracted metadata < 10 seconds after sharing the link.

### Business Success
*   **Activation Rate:** % of new users who save 5+ items in their first week.
*   **Group Multiplier:** Percentage of active users who *explicitly* add the bot to a group chat and tag it.
*   **Cost Efficiency:** Extraction cost < $0.02 per video processed (via Model Router optimizations).
*   **Privacy Trust (Zero False Positives):** 0% rate of saving untagged messages in group contexts.

### Technical Success
*   **Ingestion Latency:** Webhook acknowledgement < 3 seconds (Twilio requirement).
*   **Extraction Latency:** Video analysis completed within 30 seconds.
*   **Uptime:** 99.9% uptime for the Ingestion Service (Stateless Webhook Handler).

## Product Scope

### MVP Strategy ("The Unblocker" with Dual Context)
Phase 1 focuses on proving value in both **Personal (DM)** and **Shared (Group)** contexts with strict privacy boundaries. The MVP is a "Chat-First" experience with no external web dashboard.

**Included in MVP:**
*   **Dual Context Entry:**
    *   **DM:** Passive capture (All messages processed).
    *   **Group:** Explicit capture (Only `@VaultBot` tagged messages processed).
*   **Privacy-First Integration:** Untagged group messages are strictly ignored (Zero False Positives).
*   **Ingestion:** WhatsApp Bot receiving Text, Link (IG/TikTok), and Video messages.
*   **Metadata Engine:** Autonomous extraction of `Location`, `Price` (if explicit), `Vibe/Tags` from shared content.
*   **Semantic Search:** Natural language query interface ("/search cozy cafe") returning a list of deep links.
*   **Unified Search View:** DM Search shows Personal + Related Group items. Group Search shows Group items only.
*   **Deboucing:** "Burst" handling to prevent notification spam during content dumps.
*   **History:** Persistent storage of user items in a vector database.

**Out of Scope (Post-MVP):**
*   Web Dashboard / Visual Gallery (Phase 2)
*   User Accounts / Login (Phase 2)
*   Collaborative/Shared Lists (Phase 2)
*   Export to Notion (Phase 3)

## Implementation Status

> [!NOTE]
> **Last Updated:** 2026-02-10

### Epic 1: The "Digital Vault" (Core Ingestion & Privacy) ✅ COMPLETE

**Completed Stories:**
- ✅ **Story 1.1:** Webhook Ingestion & Privacy Gate
- ✅ **Story 1.2:** Job Queue Schema  
- ✅ **Story 1.3:** Payload Parser & Classification
- ✅ **Story 1.4:** Automatic User Profile Creation
- ✅ **Story 1.5:** Dead Letter Queue (DLQ)

**Key Achievements:**
- WhatsApp bot successfully processes DM (passive) and Group (tagged-only) messages
- Database schema supports users, jobs, and dead letter queue
- Classifier worker automatically detects content type (link, video, image, text)
- User profiles auto-created on first interaction using phone number
- Failed jobs routed to DLQ for debugging

### Epic 2: "The Analyst" (Intelligence Engine) 🚧 IN PROGRESS

**Completed Stories (5/9):**
- ✅ **Story 2.1:** Vision API Integration (OpenRouter with GPT-4o/Claude)
- ✅ **Story 2.2:** YouTube & Social Link Scraper (yt-dlp + proxy rotation)
- ✅ **Story 2.3:** Video Frame Extraction (keyframe analysis)
- ✅ **Story 2.4:** Image Post Extraction (Social Media)
- ✅ **Story 2.5:** Text & Article Parser

**In Development:**
- 🚧 **Story 2.8:** Raw Image Processing (ready-for-dev)
- 🚧 **Story 2.9:** Video Post Extraction (ready-for-dev)

**Not Started:**
- ⬜ **Story 2.6:** Data Normalizer Agent
- ⬜ **Story 2.7:** Natural Language Summary Generator

**Key Achievements:**
- Universal link scraper supports Instagram, TikTok, YouTube, blogs, articles
- YouTube dual-strategy: YouTube Data API (fast) + yt-dlp fallback (cookie-based)
- Video/image analysis via Vision API with structured metadata extraction
- Deduplication system via `link_metadata` table (url_hash)
- 5 specialized workers deployed on Cloud Run: classifier, scraper, video, image, article

### Epic 3: "Ask The Vault" (Search & Recall) ⬜ NOT STARTED

**Pending Stories:**
- ⬜ Vector Extension & Indexing
- ⬜ Search Command Parser
- ⬜ Semantic Search Implementation
- ⬜ Dynamic Card Generator
- ⬜ WhatsApp Visual Response

### Epic 4: "Shared Memories" (Group Context) ⬜ NOT STARTED

**Pending Stories:**
- ⬜ Source Attribution Logic
- ⬜ Hybrid Search Scope (RLS Policy) 
- ⬜ Group Member Sync
- ⬜ Privacy Control (/pause)

## User Journeys

### 1. Explicit Group Capture (Shared Memory)
*   **Scene:** Ananya finds an Instagram reel titled "Hidden Jazz Bar in Kyoto" and wants to share it with her "Japan Trip" group.
*   **Action:** She shares the reel in the group and explicitly tags the bot: "We MUST go here 🎷 @VaultBot".
*   **System Behavior:** Bot detects the tag. It debounces multiple messages. It extracts metadata (Location, Vibe) and saves the item to **Shared Group Memory**, attributed to Ananya.
*   **Outcome:** VaultBot reacts with 📝. The item is now searchable by anyone in that group.

### 2. Semantic Recall from Group Memory
*   **Scene:** 2 months later. Rohan (in the same group) is planning the evening.
*   **Action:** Rohan types `/search jazz kyoto` in the group chat.
*   **System Behavior:** VaultBot searches **only** the Group Memory for this specific chat. It finds the reel Ananya saved.
*   **Outcome:** Bot replies: "Found 1 match: 🎷 **Blue Note Kyoto** (Saved by Ananya 2mo ago). [Link]". Attribution builds trust.

### 3. Untagged Messages Are Ignored (Privacy)
*   **Scene:** Multiple casual links and messages are shared in the group without tagging `@VaultBot`.
*   **Action:** System receives webhooks but detects no tag.
*   **System Behavior:** System strictly ignores payload. No processing, no database writes, no reactions.
*   **Outcome:** Zero spam. Users feel safe that the bot is not "listening" to private conversations.

### 4. 1:1 DM Passive Capture (Personal Memory)
*   **Scene:** Ananya is researching solo in her DM with VaultBot.
*   **Action:** She forwards multiple links and media files directly to the bot.
*   **System Behavior:** In DM, *all* content is processed by default (Passive Capture). Items are saved to her **Personal Memory**.
*   **Outcome:** DM acts as a private scratchpad. "Saved. You can search later."

### 5. Failure With Feedback
*   **Scene:** Ananya tags VaultBot on a private Instagram account link or expired URL.
*   **Action:** Scraper fails to retrieve content.
*   **System Behavior:** Item routed to Dead Letter Queue.
*   **Outcome:** Bot replies: "⚠️ Couldn’t save this (private/unavailable). Try pasting the location name." (No silent failures).

### 6. User Control in DM (Pause/Resume)
*   **Scene:** Ananya wants to chat with the LLM without saving everything.
*   **Action:** She types `/pause`.
*   **System Behavior:** System sets user session to "Paused". Stops saving content.
*   **Outcome:** "⏸️ Paused. I won’t save messages until you /resume." Control reduces anxiety.

### 7. DM → Group Memory Migration
*   **Scene:** Ananya found a cool bar in her DM research (Personal Memory) and now wants to suggest it to the group.
*   **Action:** She forwards the link from her DM to the Group and tags `@VaultBot`.
*   **System Behavior:** System treats this as a *new* capture in the Group context. It saves a simplified copy to **Shared Group Memory**.
*   **Outcome:** Proper permission migration. Personal items stay private; explicitly shared items become group knowledge.

### 8. Group Access After Migration (Unified View)
*   **Scene:** Rohan searches in the Group. Ananya searches in her DM.
*   **Action:** Rohan: `/search jazz` (in Group). Ananya: `/search jazz` (in DM).
*   **Outcome:**
    *   **Rohan (Group):** Sees only the item Ananya explicitly shared to the group.
    *   **Ananya (DM):** Sees results from her **Personal Memory** AND **Related Groups** (Unified View). "Found 1 personal item and 1 group item."

## Innovation & Novel Patterns

### Innovation Areas
*   **"Zero UI" Interaction:** Shifting from "App-First" to "Chat-First". Reducing capture friction to near zero by leveraging the user's existing habit loop (WhatsApp Share).
*   **Hybrid Context Extraction:** Moving beyond simple link unfurling. We fuse **Platform Metadata** (Captions, Descriptions, Hashtags) with **Visual Analysis** (Frame extraction) to understand "What is this?" when the video itself is ambiguous.
*   **"Agentic Memory":** The shift from reactive storage (bookmarks) to proactive intelligence. The system remembers *for* you, turning a passive database into an active participant.

### Risk Mitigation Strategy
*   **Platform Risk:** Meta blocking the scraper. *Mitigation:* Diverse proxy rotation and fallback to "Text Save" mode.
*   **Market Risk:** "Write-Only" Behavior. *Mitigation:* Verify value via "Retrieval Rate" metric; pivot to Push reminders if needed.
*   **Privacy Perception:** Users fearing the bot reads private chats. *Mitigation:* Strict privacy policy and technical controls (reading only specific messages/commands).

## Functional Requirements

### 1. Ingestion & Capture
*   **FR-01:** System acts as a WhatsApp Bot to receive messages. **Constraint:** In DMs, process all valid content. In Groups, process *only* messages explicitly tagging `@VaultBot` (or replies to the bot).
*   **FR-02:** System debounces "burst usage" (aggregates messages sent within 60s window from same user).
*   **FR-03:** System validates URLs and identifies platform origin (IG, TikTok, YouTube, Generic Web).
*   **FR-13 (Privacy):** System MUST strictly ignore (no-op) all untagged messages in group channels.
*   **FR-14 (Attribution):** Saved items in groups MUST store the `user_id` of the sharer to display "Saved by [Name]" in search results.

### 2. Metadata Extraction (The Brain)
*   **FR-04:** System extracts **Visual Metadata** (keyframes/OCR) from both **Video and Image** files. ✅ **IMPLEMENTED** via Vision API integration (Story 2.1) and frame extraction (Story 2.3).
*   **FR-05:** System extracts **Platform Metadata** (Caption, Hashtags, Author) from valid links. ✅ **IMPLEMENTED** via dual-strategy scraper: YouTube Data API for fast metadata + yt-dlp with cookie authentication for comprehensive extraction (Story 2.2).
*   **FR-05a (NEW):** System implements **YouTube Dual Extraction Strategy**: Primary extraction via YouTube Data API (fast, quota-based), automatic fallback to yt-dlp with cookie authentication for API failures or quota exhaustion. ✅ **IMPLEMENTED**
*   **FR-06:** System generates and stores a **Natural Language Summary** for ALL content types (Video, Image, Text) to support downstream RAG retrieval. ⬜ **PLANNED** (Story 2.7)
*   **FR-07:** System normalizes data into standard fields (`Location`, `Price`, `Category`, `Vibe`). ⬜ **PLANNED** (Story 2.6)

### 3. Search & Retrieval (The Value)
*   **FR-08:** Users can query their history via natural language commands (e.g., `/search cozy cafe`).
*   **FR-09:** System performs **Semantic Search** (Vector Similarity) over visuals, summaries, and platform metadata.
*   **FR-10:** System returns a ranked list of "Unfurled" results with deep links to the original content.
*   **FR-15 (Search Scope):**
    *   **Group Search:** Returns only items saved to that specific `channel_id`.
    *   **DM Search (Unified View):** Returns items saved to user's Personal Memory (`channel_id=DM`) OR items saved to Groups the user is a member of (`user_in_group` check).

### 4. Admin & Core System
*   **FR-11:** System automatically creates a User Profile on first interaction (using Phone Number as Identity).
*   **FR-12:** Admin (and System) maintains a "Dead Letter Queue" for failed scrapes to allow for manual retry or analysis.

## API Backend Requirements

### Technical Architecture
*   **Webhook-First Design:** State of the art webhook handling for Twilio/WhatsApp integration.
*   **Authentication:**
    *   **Inbound:** Verify `X-Twilio-Signature` (HMAC-SHA1).
    *   **Internal:** API Key authentication for admin endpoints.
*   **Async Processing:** Ingestion decoupled from Processing. Webhooks return 200 OK immediately; AI work is pushed to Redis/LangGraph queue.

### Data Model
*   **Item Schema:** `id` (UUID), `user_id` (Creator), `source_channel_id` (Group ID or 'DM'), `content_type`, `source_url`, `metadata_json`, `embedding_vector`, `created_at`.
*   **Group Membership:** Track which users belong to which groups to enable "Unified Search" in DMs.
*   **User Schema:** `phone_number` (PK), `preferences_json`, `created_at`.

## Non-Functional Requirements

### Performance
*   **NFR-01 (Latency):** Webhook Endpoint must return `200 OK` within **2,000ms** (95th percentile) to prevent Twilio timeouts. ✅ **ACHIEVED**: Edge function averages <500ms
*   **NFR-02 (Throughput):** System supports **100 concurrent requests** during peak viral bursts.
*   **NFR-09 (NEW - Worker Performance):** Extraction latency targets:
    *   Link scraping: <5 seconds (yt-dlp) or <2 seconds (YouTube API)
    *   Video frame extraction: ~30-45 seconds
    *   Image analysis: ~10-15 seconds
*   **NFR-10 (NEW - Worker Uptime):** Cloud Run workers maintain >95% uptime with automatic restarts on failure.

### Security
*   **NFR-03 (Authentication):** All inbound webhooks must validate `X-Twilio-Signature`.
*   **NFR-04 (Isolation):** User data must be logically isolated via Row Level Security (RLS) in Supabase.

### Reliability
*   **NFR-05 (Scraper Resilience):** Scraper Service must maintain >90% success rate via proxy rotation and retries.
*   **NFR-06 (Data Safety):** Failed messages must be routed to a **Dead Letter Queue** (never dropped).
*   **NFR-07 (Model Fallback):** System must implement **LLM Redundancy**. If Primary Model (e.g., GPT-4o) times out or errors, automatic fallback to Backup Model (e.g., Claude 3.5 Sonnet) occurs for retryable errors.

### Scalability
*   **NFR-08 (Vector Search):** Database (pgvector) must support indexing for up to 100k items per user with <100ms query latency.
