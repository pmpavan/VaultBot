# Architecture Scoping Analysis (Gap Analysis)

**Date:** 2026-01-31
**Context:** Aligning architecture with PRD v2 (Privacy-First Group Integration).

## 1. Schema Updates (Data Model)
The current schema assumes single-user or global context. New requirements demand "Shared But Private" context.

| Feature | Requirement | Schema Change |
| :--- | :--- | :--- |
| **Group Support** | Store messages from specific groups | Add `source_channel_id` (String) to `jobs` and `items`. |
| **Attribution** | Know *who* saved an item in a group | Add `attributed_user_id` (String) / `attributed_user_name` to `items`. |
| **Context Type** | Distinguish DM vs Group | Add `source_type` ENUM (`'dm'`, `'group'`). |

## 2. Ingestion Logic Updates (Edge Function)
The "Dumb Pipe" (Webhook Handler) needs to become slightly smarter to enforce privacy *before* the queue.

*   **Current Logic:** Receive -> Queue -> Ack.
*   **New Logic (Privacy Gate):**
    ```typescript
    if (isGroupMessage) {
      if (!isTagged(message)) {
         return 200; // IGNORE (Do not queue, do not ack)
      }
    }
    // Proceed to Queue
    ```
*   **Rationale:** We must not fill the queue with untagged group chatter. This is a cost & privacy blocker.

## 3. Vector Search Logic (Scoping)
The search function currently searches *all* vectors or just *user* vectors. It needs a "Union" scope.

*   **Logic:** `Match items WHERE (user_id = me) OR (source_channel_id IN my_groups)`.
*   **Implementation:**
    *   Need a way to know `my_groups`.
    *   *MVP approach:* Pass `current_channel_id` in the search query.
        *   If searching from DM: Search `user_id = me` + (Optional: `source_type = group`).
        *   If searching from Group: Search `source_channel_id = current_channel_id`.

## 4. Privacy Control Updates
*   **Command:** `/pause`
*   **Implementation:** fastKV store (Redis or Supabase Table) to store `paused_users` set.
*   **Edge Function Check:** `if (paused_users.has(from_number)) return 200;`

## 5. Architectural Decision Records (ADR) to Add
*   **ADR-005: Privacy Gating at Edge.** (Decision: Filter at Edge, not in Agent, to save queue costs).
*   **ADR-006: Hybrid Search Scope.** (Decision: Search scope is determined by *request context*).

## Action Plan
1.  **Update `architecture.md`**:
    *   Add Schema table definitions.
    *   Update Ingestion Data Flow diagram.
    *   Define Privacy Gate logic.
