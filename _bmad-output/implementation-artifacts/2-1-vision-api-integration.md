# Story 2.1: Vision API Integration

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Developer,
```markdown
I want a unified tool to send images to an LLM (GPT-4o/Gemini) via OpenRouter,
```
So that we can extract semantic meaning from visual content.

## Acceptance Criteria

1.  **Given** a valid image URL or base64 string AND a text prompt instruction (e.g., "Describe the vibe")
2.  **When** the `vision_api` tool is called
3.  **Then** it MUST return a structured JSON response adhering to a defined Pydantic schema
4.  **And** It MUST support model switching (OpenAI GPT-4o vs Google Gemini 1.5 Pro) via configuration or runtime argument
5.  **And** It MUST handle API rate limits and retries gracefully using a backoff strategy
6.  **And** It MUST normalize errors from different providers into a standard `VisionError` exception

## Tasks / Subtasks

-   [x] **Define Data Contracts** (AC: 3)
    -   [x] Create `VisionRequest` Pydantic model (image_input, prompt, model_provider)
    -   [x] Create `VisionResponse` Pydantic model (analysis_data, usage_metadata, provider_used)
    -   [x] Define standardized `VisionError` exceptions
-   [x] **Implement Provider Adapters** (AC: 4)
    -   [x] Implement `OpenAIVisionAdapter` using `response_format={"type": "json_schema"}`
    -   [x] Implement `GeminiVisionAdapter` using `response_schema` or `response_mime_type="application/json"`
-   [x] **Implement Unified Vision Service** (AC: 2)
    -   [x] Create `VisionService` class with `analyze(request: VisionRequest) -> VisionResponse`
    -   [x] Implement model routing logic (default to config value, allow override)
    -   [x] Implement retry logic using `tenacity` or `backoff` library
-   [x] **Integration Tests** (AC: 5)
    -   [x] Create live tests with real images for both providers
    -   [x] Create mock tests for error handling and rate limits

## Dev Notes

-   **Architecture Patterns:** Adapter Pattern (for multi-provider support).
-   **Source Tree:**
    -   `agent/src/tools/vision/` (New Directory)
    -   `agent/src/tools/vision/types.py` (Contracts)
    -   `agent/src/tools/vision/service.py` (Main Entrypoint)
    -   `agent/src/tools/vision/providers/` (Adapters)
-   **Testing Standards:** Use `pytest` with `vcrpy` or mocks to avoid expensive API calls during CI.

### Project Structure Notes

-   **Alignment:** Follows the `agent/src/tools` pattern defined in `architecture.md`.
-   **Structure Decision:** We are creating a sub-package `vision/` instead of a single file `vision_api.py` to allow for clean separation of OpenAI vs Gemini logic as complexity grows.

### References

-   **Architecture:** `docs/architecture.md#Requirement-246` (Tools: `agent/src/tools/vision_api.py`)
-   **OpenAI Structured Outputs:** [OpenAI Docs](https://platform.openai.com/docs/guides/structured-outputs)
-   **Gemini JSON Mode:** [Google AI Studio Docs](https://ai.google.dev/gemini-api/docs/json-mode)

## Dev Agent Record

### Agent Model Used

Antigravity (Google DeepMind)

### Debug Log References

-   Research confirmed importance of `json_schema` for robust extraction.
-   Identified correct patterns for both GPT-4o and Gemini 1.5 Pro.

### Completion Notes List

-   Added specific Pydantic requirements to prevent "stringly typed" JSON parsing.
-   Added Adapter pattern to support the "Model Router" requirement from Architecture.
-   **Architecture Update:** Implemented Prompt Factory for centralized prompt management.
-   **Feature Update:** Integrated OpenRouter as the unified provider for both OpenAI and Gemini models.
-   **Persona Integration:** Implemented `VaultBotJsonSystemPrompt` to enforce "The Analyst" character (Concise, Witty, Objective).
-   **JSON Input:** Configured `VisionAnalyzePrompt` to compile user instructions into structured JSON for better LLM adherence.
-   **JSON System Prompts:** Refactored `VaultBotJsonSystemPrompt` to serialize strictly as a JSON object containing `persona_role`, `persona_rules`, and `format_rules`.
-   Implemented `VisionService` with `tenacity` for robust retries.

### File List

-   `agent/src/prompts/core.py`
-   `agent/src/prompts/factory.py`
-   `agent/src/prompts/vision.py`
-   `agent/src/prompts/__init__.py`
-   `agent/src/tools/vision/__init__.py`
-   `agent/src/tools/vision/types.py`
-   `agent/src/tools/vision/service.py`
-   `agent/src/tools/vision/providers/openrouter.py`
-   `tests/tools/vision/test_service_mock.py`
-   `scripts/test_vision_live.py`

