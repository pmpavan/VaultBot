"""
Data contracts for the scraper service.

This module defines Pydantic models and enums for scraper requests, responses,
and error handling. Follows the same pattern as Story 2.1 (Vision API).
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ExtractionStrategy(str, Enum):
    """Strategy used to extract metadata from a URL."""
    API = "api"  # Official platform APIs (YouTube Data API)
    YTDLP = "ytdlp"  # Social media (Instagram, TikTok, YouTube fallback)
    OPENGRAPH = "opengraph"  # Generic URLs with OpenGraph tags
    PASSTHROUGH = "passthrough"  # Blog/news articles (text extraction pending)
    VISION = "vision"  # Image analysis (Story 2.4)


class ContentType(str, Enum):
    """Type of content extracted from the URL."""
    VIDEO = "video"
    IMAGE = "image"
    ARTICLE = "article"
    LINK = "link"  # Generic link without specific content type


class ScraperRequest(BaseModel):
    """Request model for scraper service."""
    url: str = Field(..., description="URL to scrape")
    platform_hint: Optional[str] = Field(
        None,
        description="Optional hint about the platform (e.g., 'instagram', 'youtube')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "platform_hint": "youtube"
            }
        }


class ScraperResponse(BaseModel):
    """Response model for scraper service with standardized metadata."""
    # Core metadata
    title: Optional[str] = Field(None, description="Title of the content")
    description: Optional[str] = Field(None, description="Description or caption")
    author: Optional[str] = Field(None, description="Author or creator name")
    
    # Content classification
    content_type: ContentType = Field(..., description="Type of content")
    platform: str = Field(..., description="Platform name (e.g., 'youtube', 'instagram', 'blog')")
    extraction_strategy: ExtractionStrategy = Field(..., description="Strategy used for extraction")
    
    # Media metadata
    thumbnail_url: Optional[str] = Field(None, description="URL to thumbnail image")
    duration: Optional[int] = Field(None, description="Duration in seconds (for videos)")
    publish_date: Optional[str] = Field(None, description="Publication date (ISO 8601 format)")
    
    # Original URL
    raw_url: str = Field(..., description="Original URL that was scraped")
    
    # Full text content (for articles/blogs - Story 2.5)
    full_text: Optional[str] = Field(None, description="Full article text (if applicable)")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Never Gonna Give You Up",
                "description": "Official music video",
                "author": "Rick Astley",
                "content_type": "video",
                "platform": "youtube",
                "extraction_strategy": "ytdlp",
                "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
                "duration": 212,
                "publish_date": "2009-10-25T00:00:00Z",
                "raw_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


# Custom Exceptions

class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class PrivateVideoError(ScraperError):
    """Raised when attempting to scrape a private video."""
    pass


class ExpiredVideoError(ScraperError):
    """Raised when attempting to scrape an expired or deleted video."""
    pass


class UnsupportedPlatformError(ScraperError):
    """Raised when the platform is not supported."""
    pass


class ProxyError(ScraperError):
    """Raised when proxy connection fails."""
    pass


class GeoRestrictedError(ScraperError):
    """Raised when content is geo-restricted."""
    pass
