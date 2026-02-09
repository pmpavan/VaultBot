"""
yt-dlp adapter for extracting metadata from social media platforms.

Supports Instagram, TikTok, and YouTube video/image content extraction.
"""

import os
import logging
from typing import Optional
import yt_dlp

from ..types import (
    ScraperResponse,
    ContentType,
    ExtractionStrategy,
    PrivateVideoError,
    ExpiredVideoError,
    GeoRestrictedError,
    ScraperError,
)

logger = logging.getLogger(__name__)


class YtDlpExtractor:
    """Extracts metadata from social media using yt-dlp."""
    
    def __init__(self, proxy_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize yt-dlp extractor.
        
        Args:
            proxy_url: Optional proxy URL (format: http://user:pass@host:port)
            timeout: Socket timeout in seconds
        """
        self.proxy_url = proxy_url
        self.timeout = timeout
    
    def extract(self, url: str, platform: str) -> ScraperResponse:
        """
        Extract metadata from a social media URL.
        
        Args:
            url: URL to extract metadata from
            platform: Platform name (instagram, tiktok, youtube)
            
        Returns:
            ScraperResponse with extracted metadata
            
        Raises:
            PrivateVideoError: If video is private
            ExpiredVideoError: If video is deleted/expired
            GeoRestrictedError: If content is geo-restricted
            ScraperError: For other extraction errors
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,  # Get full metadata
            'skip_download': True,  # Don't download video
            'socket_timeout': self.timeout,
            # User-agent spoofing to avoid bot detection
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        # IMPORTANT: BrightData blocks YouTube, so we skip proxy for YouTube
        # Other platforms (Instagram, TikTok) can use proxy
        if self.proxy_url and platform.lower() != 'youtube':
            ydl_opts['proxy'] = self.proxy_url
            logger.info(f"Using proxy for {platform}")
        elif platform.lower() == 'youtube':
            logger.info("Skipping proxy for YouTube (BrightData blocks YouTube)")
        
        # Add cookies if available (for YouTube bot detection bypass)
        cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', '/app/cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            logger.info(f"Using cookies from {cookies_file}")
        else:
            logger.warning(f"No cookies file found at {cookies_file}. YouTube may block requests.")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ScraperError(f"No metadata extracted from {url}")
                
                return self._map_to_response(info, url, platform)
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            
            # Classify error types
            if 'private' in error_msg:
                raise PrivateVideoError(f"Video is private: {url}")
            elif 'deleted' in error_msg or 'removed' in error_msg or 'not available' in error_msg:
                raise ExpiredVideoError(f"Video has been deleted or is unavailable: {url}")
            elif 'geo' in error_msg or 'not available in your country' in error_msg:
                raise GeoRestrictedError(f"Content is geo-restricted: {url}")
            else:
                raise ScraperError(f"Failed to extract metadata: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error extracting {url}: {e}")
            raise ScraperError(f"Unexpected error: {e}")
    
    def _map_to_response(self, info: dict, url: str, platform: str) -> ScraperResponse:
        """
        Map yt-dlp info dict to ScraperResponse.
        
        Handles missing fields gracefully (AC: 8 - graceful degradation).
        """
        # Determine content type
        content_type = ContentType.VIDEO  # Default for social media
        if info.get('_type') == 'playlist':
            content_type = ContentType.VIDEO
        
        # Extract thumbnail (try multiple fields)
        thumbnail_url = (
            info.get('thumbnail') or
            info.get('thumbnails', [{}])[0].get('url') if info.get('thumbnails') else None
        )
        
        # Extract publish date
        publish_date = None
        if 'upload_date' in info:
            # Convert YYYYMMDD to ISO 8601
            upload_date = info['upload_date']
            if len(upload_date) == 8:
                publish_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}T00:00:00Z"
        
        return ScraperResponse(
            title=info.get('title'),
            description=info.get('description'),
            author=info.get('uploader') or info.get('channel'),
            content_type=content_type,
            platform=platform,
            extraction_strategy=ExtractionStrategy.YTDLP,
            thumbnail_url=thumbnail_url,
            duration=info.get('duration'),  # Already in seconds
            publish_date=publish_date,
            raw_url=url,
        )
