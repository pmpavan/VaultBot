"""
Image extraction tools for social media posts.
Supports Instagram, TikTok (Image Mode), and YouTube Community Posts.
"""

from .types import (
    ImageExtractionRequest,
    ImageExtractionResponse,
    ImageExtractionError,
    UnsupportedPlatformError,
    ProxyError,
)
