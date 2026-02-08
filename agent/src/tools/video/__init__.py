"""
Video processing tools for VaultBot.
Handles video download, frame extraction, and analysis.
"""

from .types import (
    VideoProcessingRequest,
    VideoProcessingResponse,
    VideoProcessingError,
    VideoDownloadError,
    VideoExtractionError
)
from .service import VideoProcessingService

__all__ = [
    "VideoProcessingRequest",
    "VideoProcessingResponse",
    "VideoProcessingError",
    "VideoDownloadError",
    "VideoExtractionError",
    "VideoProcessingService"
]
