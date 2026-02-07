"""
Passthrough handler for blog/news URLs.

Returns minimal metadata and signals that full text extraction is needed
downstream (Story 2.5: Text & Article Parser).
"""

import logging
from urllib.parse import urlparse

from ..types import (
    ScraperResponse,
    ContentType,
    ExtractionStrategy,
)

logger = logging.getLogger(__name__)


class PassthroughHandler:
    """Handles blog/news URLs by passing through for text extraction."""
    
    def extract(self, url: str, platform: str) -> ScraperResponse:
        """
        Create a passthrough response for blog/news URLs.
        
        Args:
            url: URL to pass through
            platform: Platform name ('blog' or 'news')
            
        Returns:
            ScraperResponse with minimal metadata and passthrough strategy
        """
        # Extract domain for basic metadata
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        return ScraperResponse(
            title=None,  # Will be extracted in Story 2.5
            description=f"Text content from {domain} - full extraction pending",
            author=None,  # Will be extracted in Story 2.5
            content_type=ContentType.ARTICLE,
            platform=platform,
            extraction_strategy=ExtractionStrategy.PASSTHROUGH,
            thumbnail_url=None,
            raw_url=url,
        )
