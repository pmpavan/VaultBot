"""
Video processing service that orchestrates download, extraction, and analysis.
"""

import tempfile
import os
import os
from typing import Optional
from .types import (
    VideoProcessingRequest,
    VideoProcessingResponse,
    VideoDownloadError,
    VideoExtractionError
)
from .processor import VideoFrameExtractor
from .downloader import DirectVideoDownloader
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
            if request.video_path:
                video_path_to_process = request.video_path
            else:
                # Step 1: Download video using DirectVideoDownloader
                downloader = DirectVideoDownloader()
                temp_video_path = downloader.download(
                    request.video_url,
                    request.auth_token,
                    request.account_sid
                )
                video_path_to_process = temp_video_path
            
            # Step 2: Extract frames
            frames, duration = self.extractor.extract_frames(video_path_to_process)
            
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
