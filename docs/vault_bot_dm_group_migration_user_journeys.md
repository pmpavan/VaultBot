# User Journeys: DM, Group Chat & DM → Group Migration

This section adds detailed user journeys reflecting finalized capture rules, shared memory semantics, and intentional migration from personal to group memory.

---

## Journey 1: Explicit Group Capture (Shared Memory)

**Persona:** Ananya  
**Context:** WhatsApp group – *“Japan Trip”*

**Scene**  
Ananya finds an Instagram reel titled *“Hidden Jazz Bar in Kyoto”*.

**Action**  
She shares the reel in the group and explicitly tags the bot:

> “We MUST go here 🎷 @VaultBot”

**System Behavior**
- Processes message only because VaultBot is tagged
- Debounces if multiple tagged messages are sent
- Extracts metadata (Location, Category, Vibe)
- Saves item to **shared group memory**
- Attributes item to **Ananya**

**Feedback**
- Bot reacts with 📝
- (First-time tip only): “I only save tagged messages in groups.”

**Outcome**
- Intentional capture
- No accidental surveillance
- Shared, searchable group memory

---

## Journey 2: Semantic Recall from Group Memory

**Persona:** Rohan  
**Context:** Same WhatsApp group, 2 months later

**Scene**  
Rohan is planning Kyoto activities.

**Action**
```
/search jazz kyoto
```

**System Response**
> 🎷 **Blue Note Kyoto**  
> *Saved by Ananya · 2 months ago*  
> [View original reel]

**Outcome**
- Any group member can retrieve shared memory
- Attribution provides trust and context

---

## Journey 3: Untagged Messages Are Ignored

**Persona:** Group members

**Scene**  
Multiple links are shared casually without tagging VaultBot.

**System Behavior**
- No processing
- No reactions
- No storage

**Outcome**
- No spam
- No accidental capture
- Reinforces explicit-intent model

---

## Journey 4: 1:1 DM Passive Capture (Personal Memory)

**Persona:** Ananya  
**Context:** 1:1 DM with VaultBot

**Scene**  
Ananya is researching Japan solo.

**Action**  
She sends links, media, and articles directly to VaultBot.

**System Behavior**
- All DM messages are recorded by default
- Meaningful content (links/media) is persisted
- Metadata extracted and indexed into **personal memory**

**Response**
> 📝 Saved. You can search later with `/search`.

**Outcome**
- DM acts as a private research scratchpad
- Zero friction, no coordination overhead

---

## Journey 5: Failure With Feedback (Non-Silent Errors)

**Persona:** Ananya  
**Context:** Group chat

**Scene**  
She tags VaultBot on a private or expired link.

**System Behavior**
- Scrape fails
- Item routed to Dead Letter Queue

**Response**
> ⚠️ Couldn’t save this (private or unavailable link). Try pasting the location name or description.

**Outcome**
- No silent failure
- Trust preserved

---

## Journey 6: User Control in DM (Pause / Resume)

**Persona:** Ananya  
**Context:** 1:1 DM

**Action**
```
/pause
```

**System Response**
> ⏸️ Paused. I won’t save messages until you `/resume`.

Later:
```
/resume
```

**Outcome**
- User retains control
- Prevents over-capture anxiety

---

## Journey 7: DM → Group Memory Migration (Personal to Shared)

**Persona:** Ananya  
**Contexts:** 1:1 DM → Group Chat

### Scene A: Personal Research in DM

Ananya sends multiple links and locations to VaultBot in DM over several days.

**System Behavior**
- Content saved to **personal memory only**
- No visibility to any group

---

### Scene B: Intentional Promotion to Group

**Action (Group Chat)**
Ananya re-shares or forwards a link into the group and tags VaultBot:

> “This is the jazz bar I found earlier 🎷 @VaultBot”

**System Behavior**
- Treats this as a new, explicit group save
- Stores item in **shared group memory**
- Attributes item to Ananya

**Feedback**
- 📝 reaction
- Optional: “Saved to group memory.”

**Outcome**
- Explicit promotion from personal → shared
- No automatic leakage
- Clean mental model

---

## Journey 8: Group Access After Migration

**Persona:** Rohan

**Action**
```
/search jazz kyoto
```

**System Response**
> 🎷 **Blue Note Kyoto**  
> *Saved by Ananya · 3 weeks ago*

**Outcome**
- Personal research becomes collective knowledge
- Group memory feels intentional and reliable

---

## Core Behavioral Rules Reinforced

- Group chats require **explicit tagging**
- Group saves form **shared memory** accessible to all current members
- DMs are **personal memory by default**
- DM content is never shared unless intentionally re-posted and tagged
- Attribution is always visible

