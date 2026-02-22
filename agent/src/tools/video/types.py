"""
Data contracts for video processing.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, model_validator


class VideoProcessingRequest(BaseModel):
    """
    Request model for video processing.
    """
    video_url: Optional[str] = Field(None, description="URL to the video file (e.g., Twilio MediaUrl)")
    video_path: Optional[str] = Field(None, description="Local path to the downloaded video file")
    message_id: str = Field(..., description="WhatsApp message ID for tracking")
    auth_token: Optional[str] = Field(None, description="Authentication token for video download (e.g., Twilio auth)")
    account_sid: Optional[str] = Field(None, description="Twilio Account SID for Basic Auth")

    @model_validator(mode='after')
    def check_url_or_path(self) -> 'VideoProcessingRequest':
        if not self.video_url and not self.video_path:
            raise ValueError("Either video_url or video_path must be provided")
        return self


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
