"""
Video processing service that orchestrates download, extraction, and analysis.
"""

import tempfile
import os
import requests
from typing import Optional
from .types import (
    VideoProcessingRequest,
    VideoProcessingResponse,
    VideoDownloadError,
    VideoExtractionError
)
from .processor import VideoFrameExtractor
from ..vision.service import VisionService
from ..vision.types import VisionRequest


class VideoProcessingService:
    """
    Service for processing videos: download, extract frames, analyze with Vision API.
    """

    def __init__(self, num_frames: int = 5):
        """
        Initialize the video processing service.
        
        Args:
            num_frames: Number of frames to extract from each video (default: 5)
        """
        self.extractor = VideoFrameExtractor(num_frames=num_frames)
        self.vision_service = VisionService()

    def download_video(
        self,
        video_url: str,
        auth_token: Optional[str] = None,
        account_sid: Optional[str] = None,
    ) -> str:
        """
        Download video from URL to temporary file.
        
        Args:
            video_url: URL to download video from
            auth_token: Optional authentication token (e.g., for Twilio)
            
        Returns:
            Path to downloaded temporary file
            
        Raises:
            VideoDownloadError: If download fails
        """
        temp_path = None
        temp_file = None
        
        try:
            # Prepare headers with authentication if provided
            headers = {}
            auth = None
            if account_sid and auth_token:
                # For Twilio MediaUrl, use HTTP Basic Auth (SID as username)
                auth = (account_sid, auth_token)
            elif auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            # Download video
            response = requests.get(video_url, headers=headers, auth=auth, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            # Determine file extension from URL or content-type
            content_type = response.headers.get('content-type', '')
            if 'mp4' in content_type or video_url.endswith('.mp4'):
                suffix = '.mp4'
            elif 'mov' in content_type or video_url.endswith('.mov'):
                suffix = '.mov'
            else:
                # Default to mp4
                suffix = '.mp4'
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = temp_file.name
            
            # Write video content
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            temp_file.close()
            
            return temp_path
            
        except requests.RequestException as e:
            # Clean up temp file on error
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            raise VideoDownloadError(f"Failed to download video from {video_url}: {str(e)}")
        except Exception as e:
            # Clean up temp file on error
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            raise VideoDownloadError(f"Unexpected error downloading video: {str(e)}")
        finally:
            # Ensure file handle is closed
            if temp_file and not temp_file.closed:
                try:
                    temp_file.close()
                except Exception:
                    pass

    def aggregate_descriptions(self, descriptions: list[str]) -> str:
        """
        Aggregate frame descriptions into a single video summary.
        
        For MVP, we concatenate descriptions with context.
        Future enhancement: Use LLM to synthesize a coherent narrative.
        
        Args:
            descriptions: List of frame descriptions
            
        Returns:
            Aggregated summary
        """
        if not descriptions:
            return "No content could be extracted from the video."
        
        if len(descriptions) == 1:
            return f"Video content: {descriptions[0]}"
        
        # Create a narrative summary
        summary_parts = ["Video content summary:"]
        
        for i, desc in enumerate(descriptions, 1):
            # Add temporal context
            if i == 1:
                summary_parts.append(f"Beginning: {desc}")
            elif i == len(descriptions):
                summary_parts.append(f"End: {desc}")
            else:
                # Calculate approximate position
                position_pct = int((i - 1) / (len(descriptions) - 1) * 100)
                summary_parts.append(f"At {position_pct}%: {desc}")
        
        return " | ".join(summary_parts)

    def process_video(self, request: VideoProcessingRequest) -> VideoProcessingResponse:
        """
        Process a video: download, extract frames, analyze, and summarize.
        
        Args:
            request: Video processing request
            
        Returns:
            Video processing response with summary
            
        Raises:
            VideoDownloadError: If download fails
            VideoExtractionError: If frame extraction fails
        """
        temp_video_path = None
        
        try:
            # Step 1: Download video
            temp_video_path = self.download_video(
                request.video_url,
                request.auth_token,
                request.account_sid
            )
            
            # Step 2: Extract frames
            frames, duration = self.extractor.extract_frames(temp_video_path)
            
            # Step 3: Analyze each frame with Vision API
            frame_descriptions = []
            
            for i, frame in enumerate(frames):
                # Convert frame to base64
                frame_base64 = VideoFrameExtractor.frame_to_base64(frame)
                
                # Create vision request
                vision_request = VisionRequest(
                    image_input=frame_base64,
                    prompt="Describe this video frame in detail. Focus on objects, actions, people, and setting. Be concise but informative.",
                    model_provider="openai"  # Default to GPT-4o
                )
                
                # Analyze frame
                vision_response = self.vision_service.analyze(vision_request)
                
                # Extract description from analysis_data
                # The structure depends on the prompt configuration
                # For now, we'll try to get a 'description' field or convert to string
                analysis_data = vision_response.analysis_data
                
                if isinstance(analysis_data, dict) and 'description' in analysis_data:
                    description = analysis_data['description']
                elif isinstance(analysis_data, dict) and 'content' in analysis_data:
                    description = analysis_data['content']
                else:
                    # Fallback: convert to string
                    description = str(analysis_data)
                
                frame_descriptions.append(description)
            
            # Step 4: Aggregate descriptions
            summary = self.aggregate_descriptions(frame_descriptions)
            
            # Return response
            return VideoProcessingResponse(
                summary=summary,
                frame_count=len(frames),
                duration=duration,
                frame_descriptions=frame_descriptions
            )
            
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                except Exception:
                    # Best effort cleanup
                    pass
