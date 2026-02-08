from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..types import ImageExtractionResponse, ImageExtractionError

class BaseExtractor(ABC):
    """Base class for all image extractors."""
    
    @abstractmethod
    def extract(self, url: str) -> ImageExtractionResponse:
        """
        Extract images and metadata from the given URL.
        
        Args:
            url: The URL to extract from.
            
        Returns:
            ImageExtractionResponse containing images and metadata.
            
        Raises:
            ImageExtractionError: If extraction fails.
        """
        pass
