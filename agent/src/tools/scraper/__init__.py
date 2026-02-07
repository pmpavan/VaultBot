"""Scraper tool for extracting metadata from URLs."""

from .types import (
    ExtractionStrategy,
    ContentType,
    ScraperRequest,
    ScraperResponse,
    ScraperError,
    PrivateVideoError,
    ExpiredVideoError,
    UnsupportedPlatformError,
    ProxyError,
    GeoRestrictedError,
)
from .service import ScraperService
from .detector import PlatformDetector

__all__ = [
    "ExtractionStrategy",
    "ContentType",
    "ScraperRequest",
    "ScraperResponse",
    "ScraperError",
    "PrivateVideoError",
    "ExpiredVideoError",
    "UnsupportedPlatformError",
    "ProxyError",
    "GeoRestrictedError",
    "ScraperService",
    "PlatformDetector",
]
