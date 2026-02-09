"""
Unified scraper service with routing and retry logic.

Main entry point for scraping URLs. Routes to appropriate extractor based on
platform detection and implements retry logic for transient failures.
"""

import os
import logging
from typing import Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .types import (
    ScraperRequest,
    ScraperResponse,
    ExtractionStrategy,
    ScraperError,
    ProxyError,
)
from .detector import PlatformDetector
from .extractors import YtDlpExtractor, OpenGraphExtractor, PassthroughHandler
from .extractors.youtube_api import YouTubeAPIExtractor
from .proxy import ProxyManager

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Unified scraper service for extracting metadata from URLs.
    
    Follows the same pattern as Story 2.1 (Vision API Service).
    """
    
    def __init__(self):
        """Initialize scraper service with all extractors."""
        self.detector = PlatformDetector()
        self.proxy_manager = ProxyManager()
        
        # Get timeouts from environment or use defaults
        ytdlp_timeout = int(os.getenv('YTDLP_TIMEOUT', '30'))
        opengraph_timeout = int(os.getenv('OPENGRAPH_TIMEOUT', '10'))
        
        # Initialize extractors
        proxy_url = self.proxy_manager.get_proxy_url()
        self.ytdlp_extractor = YtDlpExtractor(proxy_url=proxy_url, timeout=ytdlp_timeout)
        self.youtube_api_extractor = YouTubeAPIExtractor()  # Uses YOUTUBE_API_KEY env var
        self.opengraph_extractor = OpenGraphExtractor(timeout=opengraph_timeout)
        self.passthrough_handler = PassthroughHandler()
        
        logger.info("ScraperService initialized")
        if proxy_url:
            logger.info("Proxy enabled for TikTok (YouTube/Instagram blocked by BrightData)")
        if os.getenv('YOUTUBE_API_KEY'):
            logger.info("YouTube Data API enabled")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ScraperError, ProxyError)),
        reraise=True,
    )
    def scrape(self, request: ScraperRequest) -> ScraperResponse:
        """
        Scrape metadata from a URL with retry logic.
        
        Args:
            request: ScraperRequest with URL and optional platform hint
            
        Returns:
            ScraperResponse with extracted metadata
            
        Raises:
            ScraperError: If scraping fails after retries
            PrivateVideoError: If video is private
            ExpiredVideoError: If video is deleted
            GeoRestrictedError: If content is geo-restricted
            UnsupportedPlatformError: If platform is not supported
            ProxyError: If proxy connection fails
        """
        logger.info(f"Scraping URL: {request.url}")
        
        # Step 1: Detect platform and extraction strategy
        platform, content_type, strategy = self.detector.detect(
            request.url,
            request.platform_hint
        )
        
        logger.info(f"Detected: platform={platform}, content_type={content_type}, strategy={strategy}")
        
        # Step 2: Route to appropriate extractor
        try:
            # For YouTube, try API first (no bot detection), fallback to yt-dlp
            if platform.lower() == 'youtube' and os.getenv('YOUTUBE_API_KEY'):
                try:
                    logger.info("Using YouTube Data API (primary)")
                    response = self.youtube_api_extractor.extract(request.url)
                except ScraperError as e:
                    logger.warning(f"YouTube API failed, falling back to yt-dlp: {e}")
                    response = self.ytdlp_extractor.extract(request.url, platform)
            elif strategy == ExtractionStrategy.YTDLP:
                response = self.ytdlp_extractor.extract(request.url, platform)
            elif strategy == ExtractionStrategy.OPENGRAPH:
                response = self.opengraph_extractor.extract(request.url)
            elif strategy == ExtractionStrategy.PASSTHROUGH:
                response = self.passthrough_handler.extract(request.url, platform)
            else:
                raise ScraperError(f"Unsupported extraction strategy: {strategy}")
            
            logger.info(f"Successfully scraped: {request.url}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to scrape {request.url}: {e}")
            raise
