# UX Specification Gap Analysis

**Date:** 2026-01-31
**Context:** PRD updated with "Privacy-First Group" model.

## 1. Critical Gaps Identified

### A. Group Interaction Model (Privacy Conflict)
*   **PRD Requirement:** Group messages must be **explicitly tagged** (`@VaultBot`) to be saved. Untagged messages must be **strictly ignored** (FR-13).
*   **Current UX Spec:** Describes "The Forward" and "Fire and Forget" as primary. Implies passive ingestion.
*   **Impact:** Detailed UX for "Tagging" in groups is missing. The "No Feedback" rule for untagged messages needs to be explicit to avoid user confusion ("Why didn't it save?").

### B. Search Result Attribution (Shared Memory)
*   **PRD Requirement:** DM Search shows a "Unified View" (Personal + Groups). Group items must show **Attribution** ("Saved by Ananya").
*   **Current UX Spec:** Card definition includes Title, Domain, Date, and Vibe Tags. **Missing "Attribution" field.**
*   **Impact:** Users won't know *who* saved the item in a mixed list, reducing trust in the "Shared Brain" concept.

### C. User Control Commands
*   **PRD Requirement:** New commands `/pause` and `/resume` (FR-07) for DM privacy.
*   **Current UX Spec:** Only lists `/search`, `/tag`, `/help`.
*   **Impact:** Missing critical user control flows.

### D. Search Scope & Privacy
*   **PRD Requirement:** Group Search is **isolated** (only sees that group's memory).
*   **Current UX Spec:** Generic `/search` flow.
*   **Impact:** UX needs to clarify that `/search` in a Group returns different results than `/search` in a DM.

## 2. Recommended Updates

### Update `Core User Experience`
*   **Add "Dual-Context Model":** Explicitly define **DM Mode** (Passive, Private) vs **Group Mode** (Explicit, Shared).
*   **Update "Impulse Loop":** Add "The Group Tag" as a secondary impulse action.

### Update `Visual Design Foundation (The Card System)`
*   **Modify "Universal Card":** Add an **Attribution Footer** (e.g., "👤 Saved by Ananya") for items from group contexts.

### Update `User Journey Flows`
*   **Update Flow 1 (Ingestion):** Branch logic for **Group (Tag Required)** vs **DM (Auto-Save)**.
*   **Add Flow 4 (Privacy Control):** Visualizing the `/pause` interaction.
*   **Update Flow 2 (Retrieval):** Visualize "Unified View" in DM vs "Filtered View" in Group.

## 3. Action Plan
1.  **Edit** `ux-design-specification.md` to incorporate these changes.
2.  **Verify** against PRD FRs.
