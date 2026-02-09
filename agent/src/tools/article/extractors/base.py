from abc import ABC, abstractmethod
from typing import Optional

from ..types import ArticleExtractionResponse, ArticleExtractionError

class BaseArticleExtractor(ABC):
    """Base class for all article extractors."""
    
    @abstractmethod
    def extract(self, url: str, html_content: Optional[str] = None) -> ArticleExtractionResponse:
        """
        Extract article content from the given URL.
        
        Args:
            url: The URL to extract from.
            html_content: Optional pre-fetched HTML content.
            
        Returns:
            ArticleExtractionResponse containing text and metadata.
            
        Raises:
            ArticleExtractionError: If extraction fails.
        """
        pass
