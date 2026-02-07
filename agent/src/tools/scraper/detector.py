"""
Platform detector for URL classification and routing.

Detects the platform/content type of a URL and recommends the appropriate
extraction strategy.
"""

import re
from typing import Tuple
from urllib.parse import urlparse

from .types import ExtractionStrategy, ContentType


class PlatformDetector:
    """Detects platform and content type from URLs."""
    
    # Social media URL patterns
    INSTAGRAM_PATTERNS = [
        r'instagram\.com/p/',
        r'instagram\.com/reel/',
        r'instagram\.com/tv/',
    ]
    
    TIKTOK_PATTERNS = [
        r'tiktok\.com/@.*/video/',
        r'vm\.tiktok\.com/',
        r'vt\.tiktok\.com/',
    ]
    
    YOUTUBE_PATTERNS = [
        r'youtube\.com/watch',
        r'youtu\.be/',
        r'youtube\.com/shorts/',
    ]
    
    # Blog/News platform indicators
    BLOG_PLATFORMS = [
        'medium.com',
        'substack.com',
        'wordpress.com',
        'blogspot.com',
        'ghost.io',
    ]
    
    # News domains (simplified - in production, use a comprehensive list)
    NEWS_DOMAINS = [
        'nytimes.com',
        'bbc.com',
        'cnn.com',
        'reuters.com',
        'theguardian.com',
    ]
    
    def detect(self, url: str, platform_hint: str | None = None) -> Tuple[str, ContentType, ExtractionStrategy]:
        """
        Detect platform, content type, and recommended extraction strategy.
        
        Args:
            url: URL to analyze
            platform_hint: Optional hint about the platform
            
        Returns:
            Tuple of (platform_name, content_type, extraction_strategy)
        """
        # Use hint if provided and valid
        if platform_hint:
            platform_hint = platform_hint.lower()
            if platform_hint in ['instagram', 'tiktok', 'youtube']:
                return self._detect_social_media(url, platform_hint)
        
        # Detect social media platforms
        if self._matches_patterns(url, self.INSTAGRAM_PATTERNS):
            return ('instagram', ContentType.VIDEO, ExtractionStrategy.YTDLP)
        
        if self._matches_patterns(url, self.TIKTOK_PATTERNS):
            return ('tiktok', ContentType.VIDEO, ExtractionStrategy.YTDLP)
        
        if self._matches_patterns(url, self.YOUTUBE_PATTERNS):
            return ('youtube', ContentType.VIDEO, ExtractionStrategy.YTDLP)
        
        # Detect blog/news platforms
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        
        # Use exact domain matching or subdomain matching to prevent false positives
        # e.g., 'medium.com.evil.site' should NOT match 'medium.com'
        if any(domain == blog_platform or domain.endswith('.' + blog_platform) for blog_platform in self.BLOG_PLATFORMS):
            return ('blog', ContentType.ARTICLE, ExtractionStrategy.PASSTHROUGH)
        
        if any(domain == news_domain or domain.endswith('.' + news_domain) for news_domain in self.NEWS_DOMAINS):
            return ('news', ContentType.ARTICLE, ExtractionStrategy.PASSTHROUGH)
        
        # Generic fallback - use OpenGraph extraction
        return ('generic', ContentType.LINK, ExtractionStrategy.OPENGRAPH)
    
    def _matches_patterns(self, url: str, patterns: list[str]) -> bool:
        """Check if URL matches any of the given regex patterns."""
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def _detect_social_media(self, url: str, platform: str) -> Tuple[str, ContentType, ExtractionStrategy]:
        """Handle platform hint for social media."""
        # For now, assume video content for social media
        # Story 2.4 will handle image detection
        return (platform, ContentType.VIDEO, ExtractionStrategy.YTDLP)
