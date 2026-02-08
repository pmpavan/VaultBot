import logging
import re
from typing import Optional

from .types import ImageExtractionRequest, ImageExtractionResponse, ImageExtractionError, UnsupportedPlatformError
from .extractors.instagram import InstagramExtractor
from .extractors.tiktok import TikTokExtractor
from .extractors.youtube import YouTubeCommunityExtractor

logger = logging.getLogger(__name__)

class ImageExtractorService:
    """Service to route image extraction requests to the appropriate extractor."""

    def __init__(self):
        self.instagram_extractor = InstagramExtractor()
        self.tiktok_extractor = TikTokExtractor()
        self.youtube_extractor = YouTubeCommunityExtractor()

    def extract(self, request: ImageExtractionRequest) -> ImageExtractionResponse:
        """
        Extract images from the given request.
        
        Args:
            request: The extraction request containing the URL.
            
        Returns:
            ImageExtractionResponse with images and metadata.
            
        Raises:
            UnsupportedPlatformError: If the platform is not supported.
            ImageExtractionError: If extraction fails.
        """
        url = request.url
        platform = request.platform_hint or self._detect_platform(url)

        logger.info(f"Routing image extraction for {url} to {platform}")

        if platform == 'instagram':
            return self.instagram_extractor.extract(url)
        elif platform == 'tiktok':
            return self.tiktok_extractor.extract(url)
        elif platform == 'youtube':
            return self.youtube_extractor.extract(url)
        else:
            raise UnsupportedPlatformError(f"Unsupported platform: {platform}")

    def _detect_platform(self, url: str) -> str:
        """Detect the platform from the URL."""
        if 'instagram.com' in url or 'instagr.am' in url:
            return 'instagram'
        elif 'tiktok.com' in url:
            return 'tiktok'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        else:
            return 'unknown'
