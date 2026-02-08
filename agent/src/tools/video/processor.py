"""
Video frame extraction using OpenCV.
"""

import cv2
import tempfile
import os
from typing import List, Tuple
import numpy as np
from .types import VideoExtractionError


class VideoFrameExtractor:
    """
    Extracts keyframes from video files using OpenCV.
    """

    def __init__(self, num_frames: int = 5):
        """
        Initialize the frame extractor.
        
        Args:
            num_frames: Number of frames to extract (default: 5)
        """
        self.num_frames = num_frames

    def extract_frames(self, video_path: str) -> Tuple[List[np.ndarray], float]:
        """
        Extract equidistant keyframes from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Tuple of (list of frame arrays, video duration in seconds)
            
        Raises:
            VideoExtractionError: If frame extraction fails
        """
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise VideoExtractionError(f"Failed to open video file: {video_path}")
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            if total_frames == 0:
                raise VideoExtractionError("Video has no frames")
            
            # Calculate frame positions to extract
            # Extract frames at: start, 25%, 50%, 75%, end
            # Adjust num_frames based on video length
            actual_num_frames = min(self.num_frames, total_frames)
            
            if actual_num_frames == 1:
                frame_positions = [0]
            else:
                # Equidistant positions
                frame_positions = [
                    int(i * (total_frames - 1) / (actual_num_frames - 1))
                    for i in range(actual_num_frames)
                ]
            
            # Extract frames
            frames = []
            for frame_pos in frame_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()
                
                if ret:
                    frames.append(frame)
                else:
                    # If we can't read a specific frame, try to continue
                    # but log the issue
                    continue
            
            cap.release()
            
            if not frames:
                raise VideoExtractionError("Failed to extract any frames from video")
            
            return frames, duration
            
        except cv2.error as e:
            raise VideoExtractionError(f"OpenCV error during frame extraction: {str(e)}")
        except Exception as e:
            if isinstance(e, VideoExtractionError):
                raise
            raise VideoExtractionError(f"Unexpected error during frame extraction: {str(e)}")

    @staticmethod
    def frame_to_base64(frame: np.ndarray) -> str:
        """
        Convert a frame (numpy array) to base64 string for Vision API.
        
        Args:
            frame: Frame as numpy array (from OpenCV)
            
        Returns:
            Base64 encoded JPEG image string
        """
        import base64
        
        # Encode frame as JPEG
        success, buffer = cv2.imencode('.jpg', frame)
        
        if not success:
            raise VideoExtractionError("Failed to encode frame as JPEG")
        
        # Convert to base64
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{jpg_as_text}"
