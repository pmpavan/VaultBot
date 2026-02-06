---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/prd.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/architecture.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/ux-design-specification.md
---

# VaultBot - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for VaultBot, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-01: System acts as a WhatsApp Bot handling multi-modal inputs. Only processes tagged messages in Groups.
FR-02: System debounces "burst usage" (60s aggregation window).
FR-03: System validates URLs and identifies platform origin (IG, TikTok, YouTube).
FR-04: System extracts Visual Metadata (keyframes/OCR) from Video/Image files.
FR-05: System extracts Platform Metadata (Caption, Hashtags) from valid links.
FR-06: System generates Natural Language Summaries for all content.
FR-07: Data normalizer standardizes Location, Price, Category, Vibe.
FR-08: Users query history via natural language commands (/search).
FR-09: Semantic Search over visuals, summaries, and metadata.
FR-10: System returns ranked list of "Unfurled" result cards.
FR-11: Automatic User Profile creation on first interaction.
FR-12: Dead Letter Queue for failed scrapes.
FR-13 (Privacy): Strictly ignore untagged group messages (No-Op).
FR-14 (Attribution): Store `user_id` of sharer in group contexts.
FR-15 (Search Scope): Filter search by `channel_id` (Group) or `user_member_groups` (Unified DM).

### NonFunctional Requirements

NFR-01 (Latency): Webhook Ack < 2000ms.
NFR-02 (Throughput): Support 100 concurrent requests.
NFR-03 (Security): Validate X-Twilio-Signature on all inbound webhooks.
NFR-04 (Isolation): RLS enforces data isolation between users/groups.
NFR-05 (Resilience): Scraper >90% success (Proxy Rotation).
NFR-06 (Data Safety): Failed jobs route to DLQ.
NFR-07 (Fallback): LLM Redundancy (Primary -> Backup).
NFR-08 (Scale): Vector index supports 100k items < 100ms.

### Additional Requirements

**Architecture Requirements:**
- Implement "Async Brain" pattern: Supabase Edge (Ingestion) -> Postgres Queue -> LangGraph (Processing).
- Ingestion Service must be "Dumb Pipe" (No AI logic to ensure speed).
- Privacy Logic at Edge: `if (Group && !Tagged) return 200`.
- Hybrid Runtime: Deno (TS) for Edge, Python for Agent.
- Schema: Jobs table with `source_channel_id` and `source_type`.

**UX Requirements:**
- Dual Context Experience: "Fire & Forget" (DM) vs "Explicit Tag" (Group).
- Visual Cards: Generating OpenGraph images for results.
- Card Layout: Add "Saved by [Name]" footer for group items.
- Privacy Flows: Implement `/pause` and `/resume` commands with visual feedback.
- Input Feedback: Immediate Emoji Reactions ("Memo" = Ack, "Bolt" = Done).

### FR Coverage Map

FR-01: Epic 1 - Ingestion & Tagging
FR-02: Epic 1 - Debouncing
FR-03: Epic 1 - URL Validation
FR-04: Epic 2 - Visual Extraction
FR-05: Epic 2 - Platform Metadata
FR-06: Epic 2 - AI Summary
FR-07: Epic 2 - Data Normalization
FR-08: Epic 3 - Natural Language Query
FR-09: Epic 3 - Semantic Search
FR-10: Epic 3 - Visual Results (Cards)
FR-11: Epic 1 - User Profiles
FR-12: Epic 1 - Dead Letter Queue
FR-13: Epic 1 - Privacy Gating (Untagged Ignore)
FR-14: Epic 4 - Group Attribution
FR-15: Epic 4 - Hybrid Search Scope

## Epic List

### Epic 1: The "Digital Vault" (Core Ingestion & Privacy)
**Goal:** Enable users to securely "offload" content from WhatsApp to the System with reliable capture and strict privacy gates.
**User Value:** "I trust that my forwarded links are saved, and my private chats are ignored."
**FRs Covered:** FR-01, FR-02, FR-03, FR-11, FR-12, FR-13.

### Story 1.1: Webhook Ingestion & Privacy Gate

As a Group User,
I want the system to ignore my messages unless I explicitly tag it,
So that I can have private conversations without fear of being recorded.

**Acceptance Criteria:**

**Given** a WhatsApp Webhook event from a Group channel (`source_type='group'`)
**When** the message payload does NOT contain `@VaultBot` or a reply to the bot
**Then** the System MUST return `200 OK` immediately
**And** the System MUST NOT insert any job into the Queue (No-Op)

**Given** a WhatsApp Webhook event from a Group channel
**When** the message payload DOES contain `@VaultBot`
**Then** the System MUST Validate the Twilio Signature
**And** Insert a new job into the `jobs` table with `source_type='group'`
**And** React with 📝 to the user message

**Given** a WhatsApp Webhook event from a DM channel (`source_type='dm'`)
**When** any valid message is received
**Then** the System MUST Insert a new job into the `jobs` table
**And** React with 📝

### Story 1.2: Job Queue Schema

As a Developer,
I want a robust database schema for Jobs and Users,
So that we can store requests reliably and support the processing pipeline.

**Acceptance Criteria:**

**Given** a fresh Supabase instance
**When** the migration script is run
**Then** a `users` table exists with `phone_number` (PK), `first_name`, `created_at`
**And** a `jobs` table exists with `id` (UUID), `user_id` (FK), `source_channel_id`, `source_type` ('dm'|'group'), `payload` (JSONB), `status` ('pending'|'processing'|'complete'|'failed'), `created_at`
**And** RLS policies are enabled (Service Role has full access)

### Story 1.3: Payload Parser & Classification

As a System,
I want to classify incoming content as Link, Image, or Video,
So that the correct downstream agent can process it.

**Acceptance Criteria:**

**Given** a 'pending' job in the queue
**When** the Processor Node picks it up
**Then** it MUST parse the JSON payload to detect content type
**And** Identify the Platform (Instagram, TikTok, YouTube, Generic) if it is a Link
**And** Update the job `content_type` field with the result ('video', 'image', 'link', 'text')
**And** If content is unsupported, mark job as 'failed' and notify user

### Story 1.4: Automatic User Profile Creation

As a New User,
I want to start using the bot immediately without a sign-up flow,
So that I can capture content impulsively.

**Acceptance Criteria:**

**Given** a Webhook from a phone number that does not exist in `users` table
**When** the Webhook Handler processes the request
**Then** it MUST automatically Insert a new row into `users` with the `phone_number`
**And** Use the `ProfileName` from the WhatsApp payload as `first_name`
**And** Link the created Job to this new `user_id`

### Story 1.5: Dead Letter Queue (DLQ)

As an Admin,
I want failed webhooks to be saved for analysis,
So that we can debug scraping failures or edge cases.

**Acceptance Criteria:**

**Given** a Webhook processing error (e.g., Database Insert fails)
**When** the error is caught in the Edge Function
**Then** the payload MUST be sent to a separate `dlq_jobs` table (or logged to Supabase Logging)
**And** The System MUST still return `200 OK` to Twilio to prevent webhook retries/backoff

### Epic 2: "The Analyst" (Intelligence Engine)
**Goal:** Transform raw links and videos into structured "Knowledge" (Summary, Vibe, Price) using AI.
**User Value:** "The system understands the content I saved, even if I didn't type anything."
**FRs Covered:** FR-04, FR-05, FR-06, FR-07.

### Story 2.1: Vision API Integration

As a Developer,
I want a unified tool to send images to an LLM (GPT-4o/Gemini),
So that we can extract semantic meaning from visual content.

**Acceptance Criteria:**

**Given** a valid image URL or base64 string
**And** a text prompt instruction (e.g., "Describe the vibe")
**When** the `vision_api` tool is called
**Then** it MUST return a structured JSON response
**And** It MUST handle API rate limits and retries gracefully

### Story 2.2: YouTube & Social Link Scraper

As a User,
I want to save links from Instagram, TikTok, and YouTube,
So that I don't have to manually copy descriptions.

**Acceptance Criteria:**

**Given** a URL from a supported platform
**When** the Scraper Node processes it
**Then** it MUST return `title`, `description`, `author`, `duration`, and `thumbnail_url`
**And** It MUST use a proxy service to avoid IP blocks
**And** It MUST handle private/expired video errors by returning a specific error code

### Story 2.3: Video Frame Extraction

As a User,
I want the bot to "watch" the video I sent,
So that it can describe the content even if it has no caption.

**Acceptance Criteria:**

**Given** a raw video file (WhatsApp native video)
**When** the Extraction Node runs
**Then** it MUST download the video and extract 3-5 distinct keyframes
**And** Send these frames to the Vision API
**And** Aggregate the frame descriptions into a single "Video Content Summary"

### Story 2.4: Data Normalizer Agent

As a System,
I want to standardize the chaotic AI output into a clean schema,
So that we can run SQL queries on `price` and `category`.

**Acceptance Criteria:**

**Given** a raw AI description (e.g., "It looks like a pricey sushi place, maybe 100 bucks")
**When** the Normalizer Agent runs
**Then** it MUST output a JSON object: `{ "category": "Food", "price_range": "$$$", "tags": ["Sushi", "Japanese", "Date Night"] }`
**And** It MUST strictly adhere to the defined ENUMs for Category

### Story 2.5: Natural Language Summary Generator

As a User,
I want a concise summary of what I saved,
So that I can search for it using natural language later (RAG).

**Acceptance Criteria:**

**Given** all extracted metadata (OCR, Captions, Vision description)
**When** the Summarizer Node runs
**Then** it MUST generate a 2-sentence summary (e.g., "A high-end sushi restaurant in Kyoto called Blue Note, known for live jazz.")
**And** This summary MUST be stored in the `summary` column for vector embedding

### Epic 3: "Ask The Vault" (Search & Recall)
**Goal:** Enable natural language retrieval via `/search` with visual "Card" results so users can find what they saved.
**User Value:** "I can instantly find that 'jazz bar' I saved months ago."
**FRs Covered:** FR-08, FR-09, FR-10.

### Story 3.1: Vector Extension & Indexing

As a Developer,
I want to enable vector storage in the database,
So that we can perform semantic similarity searches.

**Acceptance Criteria:**

**Given** the Supabase database
**When** the migration runs
**Then** it MUST enable the `pgvector` extension
**And** Create a `vectors` table (or add column to items)
**And** Create an HNSW index for fast retrieval
**And** Create a Supabase Edge Function to generate embeddings using OpenAI `text-embedding-3-small`

### Story 3.2: Search Command Parser

As a User,
I want to type `/search jazz in kyoto`,
So that the bot knows I am looking for something.

**Acceptance Criteria:**

**Given** a webhook payload
**When** the payload body starts with `/search`
**Then** the System MUST parse the text following the command as the `search_query`
**And** Identify the context (`source_channel_id`) from the payload
**And** Trigger the Search Workflow

### Story 3.3: Semantic Search Implementation

As a User,
I want the system to find relevant items even if I don't use exact keywords,
So that I can find "cozy cafe" even if the item says "warm coffee shop".

**Acceptance Criteria:**

**Given** a `search_query`
**When** the Search Node runs
**Then** it MUST generate an embedding for the query
**And** Perform a cosine similarity search against the DB
**And** Filter results based on the User's Context (Story 4.2 covers the complex logic, this story implements basic Owner filter)
**And** Return the top 5 matches

### Story 3.4: Dynamic Card Generator (OpenGraph)

As a User,
I want to see a visual preview of the result,
So that I can recognize the video or place quickly.

**Acceptance Criteria:**

**Given** an Item with Title, Image URL, and Metadata
**When** the Card Generator Service is called (e.g., `/api/og?titl=...`)
**Then** it MUST return a dynamically generated PNG image
**And** The image MUST contain the Title, Price, Vibe Tags, and Background Image
**And** It MUST be optimized for WhatsApp Preview size (1.91:1)

### Story 3.5: WhatsApp Visual Response

As a User,
I want the search results to appear as clickable cards in the chat,
So that I can click through to the original content.

**Acceptance Criteria:**

**Given** a list of search results
**When** the Bot constructs the reply
**Then** it MUST send a message containing the "Unfurled Link" (our OG Card URL)
**And** It MUST include a deep link to the original source
**And** It MUST include a "Caption Fallback" for accessibility (Text description of the card)

### Epic 4: "Shared Memories" (Group Context)
**Goal:** Unlock the "Group Brain" by enabling shared search scopes and identifying *who* saved what.
**User Value:** "I can see what *we* saved as a group, and who recommended it."
**FRs Covered:** FR-14, FR-15.

### Story 4.1: Source Attribution Logic

As a Group User,
I want to know who saved a recommendation,
So that I can trust the source (e.g., "Oh, Ananya saved this, she has good taste").

**Acceptance Criteria:**

**Given** a Group Message being ingested
**When** the Ingestion Service processes it
**Then** it MUST capture the `user_id` (phone number) of the sender from the payload
**And** Store it in the `attributed_user_id` column of the `items` table
**And** The Card Generator MUST display "Saved by [FirstName]" in the card footer if context is Group

### Story 4.2: Hybrid Search Scope (RLS Policy)

As a User,
I want my searches to respect the privacy context I am in,
So that I don't see my private DM items when searching inside a Group.

**Acceptance Criteria:**

**Given** a Search Request
**When** the `source_type` is 'group'
**Then** the System MUST filter results where `source_channel_id` EQUALS the current group ID
**And** It MUST NOT return items from other groups or DMs

**Given** a Search Request from DM
**When** the `source_type` is 'dm'
**Then** the System MUST filter results where `user_id` EQUALS current user (Personal Memory) OR `source_channel_id` is in `user_member_groups` (Shared Memory)

### Story 4.3: Group Member Sync (Lazy Learning)

As a System,
I want to know which users belong to which groups,
So that I can include relevant group items in their personal DM search.

**Acceptance Criteria:**

**Given** any interaction from a User in a Group (Message, Tag, Command)
**When** the Ingestion Service processes the webhook
**Then** it MUST upsert a record into the `group_members` table linking `user_id` and `source_channel_id`
**And** This "Lazy Learning" must happen silently in the background
**And** Example: If Rohan tags bot in "Japan Trip", Rohan is now marked as a member of "Japan Trip"

### Story 4.4: Privacy Control (/pause)

As a User,
I want to temporarily stop the bot from saving my messages in DM,
So that I can chat with the LLM or handle sensitive info without recording it.

**Acceptance Criteria:**

**Given** a `/pause` command in DM
**When** received
**Then** the System MUST set a `paused` flag for the user session (in Redis or `users` table)
**And** React with ⏸️
**And** Subsequent messages MUST be ignored (No-Op) until `/resume` is received

**Given** a `/resume` command
**When** received
**Then** Clear the `paused` flag
**And** React with ▶️
