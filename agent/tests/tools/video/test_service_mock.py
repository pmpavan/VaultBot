"""
Mock tests for video processing service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.tools.video.service import VideoProcessingService
from src.tools.video.types import (
    VideoProcessingRequest,
    VideoDownloadError,
    VideoExtractionError
)


class TestVideoProcessingService:
    """Test suite for VideoProcessingService."""

    @patch('src.tools.video.service.requests.get')
    def test_download_video_success(self, mock_get):
        """Test successful video download."""
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'video/mp4'}
        mock_response.iter_content.return_value = [b'fake_video_data']
        mock_get.return_value = mock_response
        
        service = VideoProcessingService()
        temp_path = service.download_video('https://example.com/video.mp4')
        
        # Verify file was created
        assert temp_path.endswith('.mp4')
        assert mock_get.called

    @patch('src.tools.video.service.requests.get')
    def test_download_video_with_auth(self, mock_get):
        """Test video download with authentication token."""
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'video/mp4'}
        mock_response.iter_content.return_value = [b'fake_video_data']
        mock_get.return_value = mock_response
        
        service = VideoProcessingService()
        service.download_video(
            'https://example.com/video.mp4',
            auth_token='test_token'
        )
        
        # Verify auth header was set
        call_args = mock_get.call_args
        assert 'headers' in call_args.kwargs
        assert 'Authorization' in call_args.kwargs['headers']

    @patch('src.tools.video.service.requests.get')
    def test_download_video_failure(self, mock_get):
        """Test error handling when download fails."""
        mock_get.side_effect = Exception('Network error')
        
        service = VideoProcessingService()
        
        with pytest.raises(VideoDownloadError, match="Unexpected error downloading video"):
            service.download_video('https://example.com/video.mp4')

    def test_aggregate_descriptions_empty(self):
        """Test aggregation with no descriptions."""
        service = VideoProcessingService()
        result = service.aggregate_descriptions([])
        
        assert "No content could be extracted" in result

    def test_aggregate_descriptions_single(self):
        """Test aggregation with single description."""
        service = VideoProcessingService()
        result = service.aggregate_descriptions(['A person walking'])
        
        assert "Video content: A person walking" == result

    def test_aggregate_descriptions_multiple(self):
        """Test aggregation with multiple descriptions."""
        service = VideoProcessingService()
        descriptions = [
            'Person enters room',
            'Person sits down',
            'Person reads book',
            'Person stands up',
            'Person exits room'
        ]
        
        result = service.aggregate_descriptions(descriptions)
        
        # Verify structure
        assert 'Video content summary:' in result
        assert 'Beginning: Person enters room' in result
        assert 'End: Person exits room' in result
        assert '25%' in result or '33%' in result  # Middle frames

    @patch.object(VideoProcessingService, 'download_video')
    @patch('src.tools.video.service.VideoFrameExtractor')
    @patch('src.tools.video.service.VisionService')
    def test_process_video_success(
        self,
        mock_vision_service_class,
        mock_extractor_class,
        mock_download
    ):
        """Test successful end-to-end video processing."""
        # Mock download
        mock_download.return_value = '/tmp/fake_video.mp4'
        
        # Mock frame extraction
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        
        import numpy as np
        fake_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
        mock_extractor.extract_frames.return_value = (fake_frames, 10.0)
        mock_extractor.frame_to_base64 = MagicMock(return_value='data:image/jpeg;base64,fake')
        
        # Mock vision service
        mock_vision = MagicMock()
        mock_vision_service_class.return_value = mock_vision
        
        mock_vision_response = MagicMock()
        mock_vision_response.analysis_data = {'description': 'Test frame description'}
        mock_vision.analyze.return_value = mock_vision_response
        
        # Create service and process
        service = VideoProcessingService(num_frames=3)
        request = VideoProcessingRequest(
            video_url='https://example.com/video.mp4',
            message_id='msg_123'
        )
        
        response = service.process_video(request)
        
        # Verify response
        assert response.frame_count == 3
        assert response.duration == 10.0
        assert response.summary is not None
        assert len(response.frame_descriptions) == 3

    @patch.object(VideoProcessingService, 'download_video')
    def test_process_video_download_failure(self, mock_download):
        """Test error handling when download fails."""
        mock_download.side_effect = VideoDownloadError('Download failed')
        
        service = VideoProcessingService()
        request = VideoProcessingRequest(
            video_url='https://example.com/video.mp4',
            message_id='msg_123'
        )
        
        with pytest.raises(VideoDownloadError):
            service.process_video(request)
