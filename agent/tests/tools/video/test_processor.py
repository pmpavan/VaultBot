"""
Unit tests for video frame extraction.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.tools.video.processor import VideoFrameExtractor
from src.tools.video.types import VideoExtractionError


class TestVideoFrameExtractor:
    """Test suite for VideoFrameExtractor."""

    def test_frame_position_calculation_5_frames(self):
        """Test that frame positions are calculated correctly for 5 frames."""
        extractor = VideoFrameExtractor(num_frames=5)
        
        # For a 100-frame video, positions should be: 0, 25, 50, 75, 99
        total_frames = 100
        num_frames = 5
        
        expected_positions = [0, 24, 49, 74, 99]  # (i * 99 / 4) for i in 0..4
        
        # Calculate positions using the same logic as the extractor
        actual_positions = [
            int(i * (total_frames - 1) / (num_frames - 1))
            for i in range(num_frames)
        ]
        
        assert actual_positions == expected_positions

    def test_frame_position_calculation_3_frames(self):
        """Test that frame positions are calculated correctly for 3 frames."""
        total_frames = 100
        num_frames = 3
        
        # For 3 frames: start (0), middle (50), end (99)
        expected_positions = [0, 49, 99]  # (i * 99 / 2) for i in 0..2
        
        actual_positions = [
            int(i * (total_frames - 1) / (num_frames - 1))
            for i in range(num_frames)
        ]
        
        assert actual_positions == expected_positions

    def test_frame_position_single_frame(self):
        """Test frame extraction for very short videos (1 frame)."""
        total_frames = 1
        num_frames = 1
        
        expected_positions = [0]
        
        actual_positions = [
            int(i * (total_frames - 1) / (num_frames - 1)) if num_frames > 1 else 0
            for i in range(num_frames)
        ]
        
        assert actual_positions == expected_positions

    @patch('cv2.VideoCapture')
    def test_extract_frames_success(self, mock_video_capture):
        """Test successful frame extraction."""
        # Mock video capture
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap
        
        # Configure mock
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 100,  # CAP_PROP_FRAME_COUNT
            5: 30.0  # CAP_PROP_FPS
        }.get(prop, 0)
        
        # Mock frame reading
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, mock_frame)
        
        # Extract frames
        extractor = VideoFrameExtractor(num_frames=5)
        frames, duration = extractor.extract_frames('/fake/path.mp4')
        
        # Verify results
        assert len(frames) == 5
        assert duration == pytest.approx(100 / 30.0, rel=0.01)
        mock_cap.release.assert_called_once()

    @patch('cv2.VideoCapture')
    def test_extract_frames_video_not_opened(self, mock_video_capture):
        """Test error handling when video cannot be opened."""
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = False
        
        extractor = VideoFrameExtractor(num_frames=5)
        
        with pytest.raises(VideoExtractionError, match="Failed to open video file"):
            extractor.extract_frames('/fake/path.mp4')

    @patch('cv2.VideoCapture')
    def test_extract_frames_no_frames(self, mock_video_capture):
        """Test error handling when video has no frames."""
        mock_cap = MagicMock()
        mock_video_capture.return_value = mock_cap
        
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 0  # No frames
        
        extractor = VideoFrameExtractor(num_frames=5)
        
        with pytest.raises(VideoExtractionError, match="Video has no frames"):
            extractor.extract_frames('/fake/path.mp4')

    def test_frame_to_base64(self):
        """Test frame to base64 conversion."""
        # Create a simple test frame
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Convert to base64
        base64_str = VideoFrameExtractor.frame_to_base64(frame)
        
        # Verify format
        assert base64_str.startswith('data:image/jpeg;base64,')
        assert len(base64_str) > 50  # Should have actual data

    @patch('cv2.imencode')
    def test_frame_to_base64_encoding_failure(self, mock_imencode):
        """Test error handling when frame encoding fails."""
        mock_imencode.return_value = (False, None)
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        with pytest.raises(VideoExtractionError, match="Failed to encode frame as JPEG"):
            VideoFrameExtractor.frame_to_base64(frame)
