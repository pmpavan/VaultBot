"""
Tests for video processor node.
"""

import pytest
from unittest.mock import Mock, patch
from src.nodes.video_processor import VideoProcessorNode, create_video_processor_node
from src.tools.video.types import VideoProcessingResponse


class TestVideoProcessorNode:
    """Test suite for VideoProcessorNode."""

    @patch('src.nodes.video_processor.VideoProcessingService')
    def test_node_success(self, mock_service_class):
        """Test successful video processing through node."""
        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock response
        mock_response = VideoProcessingResponse(
            summary="Test video summary",
            frame_count=5,
            duration=10.0,
            frame_descriptions=["Frame 1", "Frame 2", "Frame 3", "Frame 4", "Frame 5"]
        )
        mock_service.process_video.return_value = mock_response
        
        # Create node
        node = VideoProcessorNode(num_frames=5)
        
        # Create state
        state = {
            "job_id": "job_123",
            "video_url": "https://example.com/video.mp4",
            "message_id": "msg_123",
            "auth_token": None,
            "video_summary": None,
            "error": None
        }
        
        # Process
        result = node(state)
        
        # Verify
        assert result["video_summary"] == "Test video summary"
        assert result["error"] is None
        assert mock_service.process_video.called

    @patch('src.nodes.video_processor.VideoProcessingService')
    def test_node_error_handling(self, mock_service_class):
        """Test error handling in node."""
        # Mock service to raise error
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.process_video.side_effect = Exception("Processing failed")
        
        # Create node
        node = VideoProcessorNode(num_frames=5)
        
        # Create state
        state = {
            "job_id": "job_123",
            "video_url": "https://example.com/video.mp4",
            "message_id": "msg_123",
            "auth_token": None,
            "video_summary": None,
            "error": None
        }
        
        # Process
        result = node(state)
        
        # Verify error was captured
        assert result["video_summary"] is None
        assert result["error"] is not None
        assert "Processing failed" in result["error"]

    def test_create_video_processor_node(self):
        """Test factory function."""
        node = create_video_processor_node(num_frames=3)
        
        assert isinstance(node, VideoProcessorNode)
        assert node.service is not None
