from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

ArticleContentType = Literal['article', 'blog', 'documentation', 'generic']

class ArticleExtractionRequest(BaseModel):
    """Request model for article extraction."""
    url: str
    content_type_hint: Optional[ArticleContentType] = None
    extract_images: bool = False  # Whether to try extracting main image URL

class ArticleExtractionResponse(BaseModel):
    """Response model for article extraction."""
    text: str = Field(description="Main text content of the article")
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    site_name: Optional[str] = None
    
    metadata: Dict = Field(default_factory=dict, description="Raw extracted metadata")
    og_tags: Dict[str, str] = Field(default_factory=dict, description="OpenGraph tags found")
    
    content_type: ArticleContentType = 'generic'
    
    is_paywall: bool = False
    is_partial: bool = False
    
    language: Optional[str] = None
    url: str

class ArticleExtractionError(Exception):
    """Base exception for article extraction errors."""
    pass

class UnsupportedPlatformError(ArticleExtractionError):
    """Raised when the platform/site is known to be unsupported."""
    pass

class ProxyError(ArticleExtractionError):
    """Raised when proxy connection fails."""
    pass

class ExtractionFailedError(ArticleExtractionError):
    """Raised when extraction logic fails."""
    pass
