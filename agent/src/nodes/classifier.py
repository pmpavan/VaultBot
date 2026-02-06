"""
Payload Parser & Classification Node
Story: 1.3 - Payload Parser & Classification

This module classifies incoming WhatsApp webhook payloads into content types
and identifies platform origins for link-based content.
"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse


class ContentClassifier:
    """Classifies WhatsApp webhook payloads by content type and platform."""
    
    # Platform regex patterns
    PLATFORM_PATTERNS = {
        'youtube': re.compile(
            r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/\s]{11})',
            re.IGNORECASE
        ),
        'instagram': re.compile(
            r'instagram\.com/(?:p|reels|reel)/([a-zA-Z0-9_-]+)',
            re.IGNORECASE
        ),
        'tiktok': re.compile(
            r'tiktok\.com/(?:@[\w.-]+/video/|v/|t/|[\w.-]+/|)([\w.-]+)',
            re.IGNORECASE
        ),
        'udemy': re.compile(
            r'udemy\.com/course/([a-zA-Z0-9_-]+)',
            re.IGNORECASE
        ),
        'coursera': re.compile(
            r'coursera\.org/(?:learn|specializations|professional-certificates)/([a-zA-Z0-9_-]+)',
            re.IGNORECASE
        ),
    }
    
    # URL detection pattern
    URL_PATTERN = re.compile(
        r'https?://[^\s]+',
        re.IGNORECASE
    )
    
    def detect_content_type(self, payload: Dict) -> Tuple[str, Optional[str]]:
        """
        Detect content type from Twilio WhatsApp webhook payload.
        
        Args:
            payload: Twilio webhook payload dictionary
            
        Returns:
            Tuple of (content_type, platform)
            - content_type: 'video', 'image', 'link', or 'text'
            - platform: Platform name for links, None otherwise
        """
        num_media = int(payload.get('NumMedia', 0))
        
        # Check for media attachments
        if num_media > 0:
            media_content_type = payload.get('MediaContentType0', '')
            
            if media_content_type.startswith('video/'):
                return ('video', None)
            elif media_content_type.startswith('image/'):
                return ('image', None)
            else:
                # Unsupported media type
                return ('text', None)
        
        # No media - check for URLs in message body
        body = payload.get('Body', '')
        
        if self.URL_PATTERN.search(body):
            platform = self.identify_platform(body)
            return ('link', platform)
        
        # Plain text message
        return ('text', None)
    
    def identify_platform(self, text: str) -> str:
        """
        Identify platform from URL in text.
        
        Args:
            text: Message body containing URL
            
        Returns:
            Platform name ('youtube', 'instagram', 'tiktok', 'udemy', 
            'coursera', or 'generic')
        """
        for platform, pattern in self.PLATFORM_PATTERNS.items():
            if pattern.search(text):
                return platform
        
        return 'generic'


def classify_job_payload(payload: Dict) -> Dict[str, Optional[str]]:
    """
    Classify a job payload and return content_type and platform.
    
    Args:
        payload: Twilio webhook payload from jobs table
        
    Returns:
        Dictionary with 'content_type' and 'platform' keys
    """
    classifier = ContentClassifier()
    content_type, platform = classifier.detect_content_type(payload)
    
    return {
        'content_type': content_type,
        'platform': platform
    }
