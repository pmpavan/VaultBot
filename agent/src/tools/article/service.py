import logging
from typing import Optional

from .types import ArticleExtractionRequest, ArticleExtractionResponse, ArticleExtractionError
from .extractors.trafilatura_extractor import TrafilaturaExtractor
from .extractors.newspaper_extractor import NewspaperExtractor
from .classifier import ContentClassifier

logger = logging.getLogger(__name__)

class ArticleService:
    """Unified service for article extraction."""
    
    def __init__(self):
        self.trafilatura = TrafilaturaExtractor()
        self.newspaper = NewspaperExtractor()
        self.classifier = ContentClassifier()
        
    def extract(self, request: ArticleExtractionRequest) -> ArticleExtractionResponse:
        """
        Extract article content using primary extractor with fallback.
        """
        url = request.url
        response = None
        error = None
        
        # Try Primary Extractor (Trafilatura)
        try:
            response = self.trafilatura.extract(url)
        except Exception as e:
            logger.warning(f"Trafilatura failed for {url}: {e}. Retrying with Newspaper4k.")
            error = e
            
        # Try Fallback Extractor (Newspaper4k)
        if not response:
            try:
                response = self.newspaper.extract(url)
            except Exception as e:
                logger.error(f"Newspaper4k failed for {url}: {e}")
                # Re-raise the original error if both failed, or a generic one
                raise ArticleExtractionError(f"All extraction methods failed. Last error: {e}")
        
        # Refine Classification
        if response:
            try:
                content_type = self.classifier.classify(url, None, response.title)
                response.content_type = content_type
            except Exception as e:
                 logger.error(f"Classification failed for {url}: {e}")
                 # Keep default 'generic' but add error to metadata for observability
                 if not response.metadata:
                     response.metadata = {}
                 response.metadata['classification_error'] = str(e)

        return response
