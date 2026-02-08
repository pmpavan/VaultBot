from typing import Dict, Any
import tenacity
from .types import VisionRequest, VisionResponse, VisionProviderError, VisionRateLimitError
from .providers.openrouter import OpenRouterVisionAdapter

class VisionService:
    """
    Service for analyzing images using Vision APIs.
    Handlers retries and provider selection.
    """

    def __init__(self):
        # Initialize adapter. In future we could load multiple providers here.
        # For now, OpenRouter handles all supported models.
        self.adapter = OpenRouterVisionAdapter()

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type((VisionRateLimitError, VisionProviderError)),
        reraise=True
    )
    def analyze(self, request: VisionRequest) -> VisionResponse:
        """
        Analyzes an image with automatic retries.
        """
        try:
            return self.adapter.analyze(request)
        except Exception as e:
            # Map specific exceptions if needed, otherwise bubble up
            # In a real implementation, we might inspect 'e' to see if it's a 429
            # and raise VisionRateLimitError to trigger tenacity
            raise e

# Validating Imports for Factory
from prompts import PromptFactory 
# Ensure prompts are registered implicitly via import in __init__ or manual registration if dynamic
