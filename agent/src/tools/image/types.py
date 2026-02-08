from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl

class ImageExtractionRequest(BaseModel):
    """Request model for image extraction."""
    url: str
    platform_hint: Optional[str] = None
    message_id: Optional[str] = None

class ImageExtractionResponse(BaseModel):
    """Response model for image extraction."""
    images: List[bytes] = Field(default_factory=list, description="List of image contents as bytes")
    metadata: Dict = Field(default_factory=dict, description="Extracted metadata (caption, author, etc)")
    platform: str
    image_urls: List[str] = Field(default_factory=list, description="Original URLs of the images")

class ImageExtractionError(Exception):
    """Base exception for image extraction errors."""
    pass

class UnsupportedPlatformError(ImageExtractionError):
    """Raised when the platform is not supported."""
    pass

class ProxyError(ImageExtractionError):
    """Raised when proxy connection fails."""
    pass
