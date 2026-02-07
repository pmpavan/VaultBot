from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field

class VisionRequest(BaseModel):
    """
    Request model for Vision API analysis.
    """
    image_input: str = Field(..., description="Image URL or Base64 string")
    prompt: str = Field(..., description="Instruction for analysis")
    model_provider: Literal["openai", "gemini"] = Field(
        "openai", 
        description="Model provider to use (default: openai)"
    )
    # Optional prompt configuration override
    prompt_config: Optional[Dict[str, Any]] = Field(None, description="Additional prompt configuration")

class VisionResponse(BaseModel):
    """
    Response model for Vision API analysis.
    """
    analysis_data: Dict[str, Any] = Field(..., description="Structured analysis result")
    provider_used: str = Field(..., description="Provider that processed the request")
    usage_metadata: Optional[Dict[str, Any]] = Field(None, description="Token usage, etc.")
    raw_response: Optional[Any] = Field(None, description="Raw provider response (for debugging)")

class VisionError(Exception):
    """Base exception for Vision Service errors."""
    pass

class VisionProviderError(VisionError):
    """Error raised by a specific provider."""
    pass

class VisionRateLimitError(VisionError):
    """Error raised when rate limit is exceeded."""
    pass

class VisionValidationError(VisionError):
    """Error raised when validation fails."""
    pass
