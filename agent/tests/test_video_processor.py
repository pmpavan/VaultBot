"""
Unit tests for Video Processor Node
Story: 2.3 - Video Frame Extraction
"""

import unittest
from unittest.mock import MagicMock, patch
from nodes.video_processor import VideoProcessorNode, VideoProcessorState, create_video_processor_graph
from tools.video import VideoProcessingResponse

class TestVideoProcessorNode(unittest.TestCase):
    
    def setUp(self):
        self.node = VideoProcessorNode()
        # Mock the service
        self.node.service = MagicMock()

    def test_processing_flow(self):
        """Test successful video processing flow."""
        # Setup mock return
        mock_response = VideoProcessingResponse(
            video_path="/tmp/video.mp4",
            frames=[],
            analysis=[],
            summary="A test video summary",
            frame_count=5
        )
        self.node.service.process_video.return_value = mock_response

        # Input state
        state: VideoProcessorState = {
            "job_id": "test_job",
            "video_url": "http://example.com/video.mp4",
            "message_id": "msg_123",
            "auth_token": "token",
            "account_sid": "sid",
            "video_summary": None,
            "error": None
        }

        # Execute
        result = self.node(state)

        # Verify
        self.assertEqual(result["video_summary"], "A test video summary")
        self.assertIsNone(result["error"])
        self.node.service.process_video.assert_called_once()
        
    def test_error_handling(self):
        """Test error handling in processing."""
        # Setup mock to raise exception
        self.node.service.process_video.side_effect = Exception("Download failed")

        # Input state
        state: VideoProcessorState = {
            "job_id": "test_job",
            "video_url": "http://example.com/video.mp4",
            "message_id": "msg_123",
            "auth_token": None,
            "account_sid": None,
            "video_summary": None,
            "error": None
        }

        # Execute
        result = self.node(state)

        # Verify
        self.assertIsNone(result["video_summary"])
        self.assertIn("Download failed", result["error"])

    def test_graph_execution(self):
        """Test execution via LangGraph."""
        graph = create_video_processor_graph()
        
        # We need to patch the node instance created inside create_video_processor_graph
        # effectively or patch the class
        with patch('nodes.video_processor.VideoProcessorNode') as MockNodeClass:
            mock_instance = MockNodeClass.return_value
            
            # Define side effect for the mock instance call
            def mock_call(state):
                return {
                    **state,
                    "video_summary": "Graph Summary",
                    "error": None
                }
            mock_instance.side_effect = mock_call
            
            # Re-create graph to use the mock
            graph = create_video_processor_graph()
            
            state: VideoProcessorState = {
                "job_id": "graph_job",
                "video_url": "http://example.com/video.mp4",
                "message_id": "msg_graph",
                "auth_token": None,
                "account_sid": None,
                "video_summary": None,
                "error": None
            }
            
            result = graph.invoke(state)
            
            self.assertEqual(result["video_summary"], "Graph Summary")
            self.assertIsNone(result["error"])

if __name__ == '__main__':
    unittest.main()
