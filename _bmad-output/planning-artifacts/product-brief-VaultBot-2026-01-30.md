---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/brainstorming/brainstorming-session-2026-01-30.md
  - /Users/apple/P1/Projects/Web/VaultBot/_bmad-output/planning-artifacts/research/technical-Video and Image Metadata Extraction for WhatsApp Content-research-2026-01-30.md
  - /Users/apple/P1/Projects/Web/VaultBot/docs/The Architecture of Information Fragmentation_ A Technical and Market Evaluation of MicroSaaS Solutions for Messaging-Based Content Organization.md
date: 2026-01-30
author: Pavan
---

# Product Brief: VaultBot

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

VaultBot eliminates the 'Digital Dumping Ground' effect in messaging apps. By autonomously extracting structured metadata (Location, Price, Vibe) from unstructured rich media (Instagram Reels, TikToks) shared in WhatsApp, it transforms a chaotic chat history into a queryable 'Shared Brain' for travel and lifestyle planning. It bridges the gap between the ease of capturing inspiration and the difficulty of retrieving it for decision-making.

---

## Core Vision

### Problem Statement

**Time-Shifted Retrieval Friction:** Users effortlessly share ("dump") content in moments of inspiration (System 1), but struggle to retrieve it during moments of decision-making (System 2) weeks later.
**Rich Media Blindness:** Native search in messaging apps cannot index the contents of video or image files. A reel of a "Hidden Jazz Bar in Tokyo" is invisible to a text search for "Jazz" or "Tokyo", effectively rendering the saved content useless.

### Problem Impact

*   **Decision Paralysis:** Information needed for planning is scattered and unsearchable, leading to abandoned plans.
*   **Content Graveyards:** Chat histories become cluttered with links that are never revisited.
*   **Cognitive Load:** Users are forced to manually maintain external lists (Notes/Notion) or scroll endlessly, breaking the flow of conversation.

### Why Existing Solutions Fall Short

*   **Pocket/Raindrop:** Isolate the user (single-player) and require leaving the chat context. They store the *link*, not the *meaning*.
*   **Notion/Docs:** Too much friction for "in-the-moment" capture. High setup cost ("Blank Page Syndrome").
*   **Native "Star" Features:** Do not offer semantic search or categorization; they just create a smaller, unorganized pile.

### Proposed Solution

**VaultBot: The Memory Prosthetic**
An AI-powered participant in your WhatsApp group that:
1.  **Ingests** shared media automatically (Zero-Click).
2.  **Extracts** structured data (Metadata Engine) from video/text.
3.  **Indexes** content for semantic retrieval ("Show me affordable date spots").
4.  **Organizes** it into a "Shared Brain" accessible to all group members.

### Key Differentiators

*   **Zero-Friction Ingestion:** Lives where the conversation happens. No app switching required.
*   **Rich Media Intelligence:** Unlocks data from video/images that competitors treat as opaque blobs.
*   **Social-Native:** Built for groups/couples, not just individuals. Solves the *coordination* problem, not just the *storage* problem.

## Target Users

### Primary Users

**User A: Ananya, The "Inspo-Dumper" (The Capturer)**
*   **Profile:** 28, works in creative field, active on Instagram/TikTok 2+ hours/day. System 1 Thinker (Intuitive).
*   **Behavior:** Shares content impulsively to WhatsApp groups ("We MUST go here!") directly from the feed.
*   **Pain Point:** "Write-only memory." She shares 20 things but can never find them again when actually planning the output.
*   **Motivation:** Wants to feel "organized" without actually doing the work of organizing.
*   **Aha Moment:** When she sends a raw video link and the bot replies seconds later with "Saved: Hidden Rooftop Bar, Tokyo - ¥2000 cocktails."

**User B: Rohan, The "Logistics Lead" (The Retriever)**
*   **Profile:** 31, works in tech/ops, prefers spreadsheets/Notion. System 2 Thinker (Analytical).
*   **Behavior:** The one responsible for the itinerary. Dreads the "dump" because it creates homework for him.
*   **Pain Point:** Extracting data from Ananya's unstructured inputs. He has to watch the reel to find out *where* it is.
*   **Motivation:** Efficiency. He wants a clean database he can query.
*   **Aha Moment:** When he types "/search dinner Tokyo" and gets a structured list of 5 places Ananya sent over the last 6 months.

### User Journey

1.  **Discovery:** Rohan adds VaultBot to their shared "Japan 2026" group.
2.  **Onboarding (Zero-Friction):** Ananya continues her normal behavior—sharing a reel from Instagram.
3.  **Core Interaction:**
    *   *Trigger:* Ananya shares a Reel.
    *   *Action:* VaultBot reads the video, extracts "Sushi Bar Yasuda", and saves it.
    *   *Feedback:* Bot reacts with a 📝 emoji (silent confirmation).
4.  **Success Moment:** Three weeks later, they are in Tokyo. Rohan asks "Where was that sushi place?" VaultBot replies instantly with the location pin and the original video link.

## Success Metrics

### North Star Metric
**Retrieval Factor:** The percentage of saved items that are subsequently "retrieved" (searched for, viewed, or clicked) within 30 days.
*   *Why:* Proves we are solving the "Write-Only Memory" problem. If users save but never look, we are just another digital hoarding tool.

### User Success Metrics
*   **Interpretation Accuracy (>90%):** The rate at which the AI correctly identifies the "Core Subject" (e.g., "This is a restaurant" vs "This is a cat video").
*   **Time-to-Value:** Users should receive the "Stored Confirmation" with extracted metadata < 10 seconds after sharing the link.

### Business Metrics
*   **Group Multiplier:** Percentage of active users who add the bot to a group chat with >2 participants. (Validates the social/viral loop).
*   **Activation Rate:** % of new users who save 5+ items in their first week.

## MVP Scope

### Core Features

1.  **Ingestion:** WhatsApp Bot that accepts links (IG/TikTok) and raw text.
2.  **Metadata Engine:** AI that extracts 3 fields: `Location`, `Price` (if mentioned), `Vibe/Tags`.
3.  **Semantic Search:** User types "/search cozy cafe" and gets a list of links.
4.  **Debounced Replies:** Bot doesn't spam. It waits for the "burst" to end, then sends 1 summary message.

### Out of Scope for MVP

1.  **Collaborative Trip Planning UI:** No drag-and-drop itinerary builder. (We are the *database*, not the *canvas*).
2.  **User Accounts / Login:** Using phone number only. No email/password.
3.  **Payments:** Free beta.
4.  **B2B Inventory Features:** (The Jewelry use case is deferred).
5.  **Multi-Platform:** WhatsApp Only. (No Telegram/Slack yet).

### Future Vision

"VaultBot becomes the *backend API* for your life. You dump content into WhatsApp, and we auto-populate your Notion, Google Maps, and Calendar."
