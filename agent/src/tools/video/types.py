"""
Data contracts for video processing.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class VideoProcessingRequest(BaseModel):
    """
    Request model for video processing.
    """
    video_url: str = Field(..., description="URL to the video file (e.g., Twilio MediaUrl)")
    message_id: str = Field(..., description="WhatsApp message ID for tracking")
    auth_token: Optional[str] = Field(None, description="Authentication token for video download (e.g., Twilio auth)")


class VideoProcessingResponse(BaseModel):
    """
    Response model for video processing.
    """
    summary: str = Field(..., description="Aggregated summary of video content from frame analysis")
    frame_count: int = Field(..., description="Number of frames extracted and analyzed")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    frame_descriptions: Optional[List[str]] = Field(None, description="Individual frame descriptions (optional)")


class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    pass


class VideoDownloadError(VideoProcessingError):
    """Error raised when video download fails."""
    pass


class VideoExtractionError(VideoProcessingError):
    """Error raised when frame extraction fails."""
    pass
