"""
YouTube Data API v3 extractor for metadata.

Uses official YouTube API instead of yt-dlp to avoid bot detection.
Requires YOUTUBE_API_KEY environment variable.
"""

import os
import logging
import re
from typing import Optional
from datetime import datetime
import requests

from ..types import (
    ScraperResponse,
    ContentType,
    ExtractionStrategy,
    ScraperError,
)

logger = logging.getLogger(__name__)


class YouTubeAPIExtractor:
    """Extracts metadata from YouTube using official Data API v3."""
    
    API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube API extractor.
        
        Args:
            api_key: YouTube Data API key (or set YOUTUBE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            logger.warning("No YOUTUBE_API_KEY found. YouTube API extraction will fail.")
    
    def extract(self, url: str) -> ScraperResponse:
        """
        Extract metadata from YouTube URL using Data API.
        
        Args:
            url: YouTube URL (youtube.com/watch?v=... or youtu.be/...)
            
        Returns:
            ScraperResponse with extracted metadata
            
        Raises:
            ScraperError: If API key missing or extraction fails
        """
        if not self.api_key:
            raise ScraperError("YouTube API key not configured. Set YOUTUBE_API_KEY environment variable.")
        
        # Extract video ID from URL
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ScraperError(f"Could not extract video ID from URL: {url}")
        
        # Call YouTube API
        try:
            response = requests.get(
                f"{self.API_BASE_URL}/videos",
                params={
                    'part': 'snippet,contentDetails,statistics',
                    'id': video_id,
                    'key': self.api_key,
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if 'items' not in data or len(data['items']) == 0:
                raise ScraperError(f"Video not found: {video_id}")
            
            return self._map_to_response(data['items'][0], url)
            
        except requests.RequestException as e:
            logger.error(f"YouTube API request failed: {e}")
            raise ScraperError(f"YouTube API request failed: {e}")
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.
        
        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """
        Parse ISO 8601 duration to seconds.
        
        Example: PT1H2M10S -> 3730 seconds
        """
        if not duration_str:
            return None
        
        # Simple regex for PT#H#M#S format
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return None
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _map_to_response(self, item: dict, url: str) -> ScraperResponse:
        """Map YouTube API response to ScraperResponse."""
        snippet = item.get('snippet', {})
        content_details = item.get('contentDetails', {})
        
        # Parse duration
        duration = self._parse_duration(content_details.get('duration'))
        
        # Get best thumbnail
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_url = (
            thumbnails.get('maxres', {}).get('url') or
            thumbnails.get('high', {}).get('url') or
            thumbnails.get('medium', {}).get('url') or
            thumbnails.get('default', {}).get('url')
        )
        
        # Parse publish date
        publish_date = snippet.get('publishedAt')  # Already ISO 8601
        
        return ScraperResponse(
            title=snippet.get('title'),
            description=snippet.get('description'),
            author=snippet.get('channelTitle'),
            content_type=ContentType.VIDEO,
            platform='youtube',
            extraction_strategy=ExtractionStrategy.API,
            thumbnail_url=thumbnail_url,
            duration=duration,
            publish_date=publish_date,
            raw_url=url,
        )
