"""
Integration test for video processing with a sample video file.
This test requires a real video file and Vision API access.
"""

import pytest
import os
import cv2
import numpy as np
import tempfile
from src.tools.video.service import VideoProcessingService
from src.tools.video.types import VideoProcessingRequest


def create_test_video(duration_seconds: int = 2, fps: int = 10) -> str:
    """
    Create a simple test video file for integration testing.
    
    Args:
        duration_seconds: Video duration in seconds
        fps: Frames per second
        
    Returns:
        Path to created video file
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_path = temp_file.name
    temp_file.close()
    
    # Video properties
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Create video writer
    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
    
    # Generate frames with changing content
    total_frames = duration_seconds * fps
    for i in range(total_frames):
        # Create frame with changing color
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add some variation: change color over time
        color_value = int(255 * i / total_frames)
        frame[:, :] = (color_value, 100, 255 - color_value)
        
        # Add frame number text
        cv2.putText(
            frame,
            f'Frame {i}',
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        
        out.write(frame)
    
    out.release()
    
    return temp_path


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv('OPENROUTER_API_KEY') is None,
    reason="Requires OPENROUTER_API_KEY environment variable"
)
class TestVideoProcessingIntegration:
    """Integration tests for video processing with real video files."""

    def test_process_local_video(self):
        """Test processing a locally created video file."""
        # Create test video
        video_path = create_test_video(duration_seconds=2, fps=10)
        
        try:
            # Create service
            service = VideoProcessingService(num_frames=3)
            
            # Create request (using file:// URL for local file)
            request = VideoProcessingRequest(
                video_url=f'file://{video_path}',
                message_id='test_msg_123'
            )
            
            # Process video
            # Note: This will make real Vision API calls
            response = service.process_video(request)
            
            # Verify response
            assert response.frame_count == 3
            assert response.duration is not None
            assert response.duration > 0
            assert response.summary is not None
            assert len(response.summary) > 0
            assert response.frame_descriptions is not None
            assert len(response.frame_descriptions) == 3
            
            # Verify each description has content
            for desc in response.frame_descriptions:
                assert len(desc) > 0
            
        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.unlink(video_path)

    def test_frame_extraction_accuracy(self):
        """Test that frame extraction positions are accurate."""
        video_path = create_test_video(duration_seconds=2, fps=10)
        
        try:
            from src.tools.video.processor import VideoFrameExtractor
            
            extractor = VideoFrameExtractor(num_frames=5)
            frames, duration = extractor.extract_frames(video_path)
            
            # Verify we got the expected number of frames
            assert len(frames) == 5
            
            # Verify duration is approximately correct
            assert 1.5 < duration < 2.5  # Allow some tolerance
            
            # Verify frames are valid numpy arrays
            for frame in frames:
                assert isinstance(frame, np.ndarray)
                assert frame.shape == (480, 640, 3)
            
        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)


if __name__ == '__main__':
    # Allow running this test directly for manual verification
    print("Creating test video...")
    video_path = create_test_video(duration_seconds=2, fps=10)
    print(f"Test video created at: {video_path}")
    
    print("\nExtracting frames...")
    from src.tools.video.processor import VideoFrameExtractor
    extractor = VideoFrameExtractor(num_frames=5)
    frames, duration = extractor.extract_frames(video_path)
    
    print(f"Extracted {len(frames)} frames from {duration:.2f}s video")
    
    # Cleanup
    os.unlink(video_path)
    print("Test complete!")
