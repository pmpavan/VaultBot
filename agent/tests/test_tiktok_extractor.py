import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tools.image.extractors.tiktok import TikTokExtractor
from tools.image.types import ImageExtractionResponse, ImageExtractionError


class TestTikTokExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = TikTokExtractor()
        self.extractor.proxy_manager = MagicMock()
        self.extractor.proxy_manager.get_proxy_url.return_value = "http://proxy:8080"
    
    @patch('tools.image.extractors.tiktok.yt_dlp.YoutubeDL')
    @patch('tools.image.extractors.tiktok.requests.get')
    def test_slideshow_extraction(self, mock_requests_get, mock_ytdl_class):
        """Test extraction of TikTok slideshow."""
        # Mock yt-dlp response
        mock_ytdl = MagicMock()
        mock_info = {
            'thumbnails': [
                {'url': 'https://example.com/thumb1.jpg'},
                {'url': 'https://example.com/thumb2.jpg'}
            ],
            'description': 'Test slideshow',
            'uploader': 'testuser',
            'upload_date': '20260209',
            'id': 'test123'
        }
        mock_ytdl.extract_info.return_value = mock_info
        mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl
        
        # Mock image download
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        
        # Extract
        result = self.extractor.extract("https://www.tiktok.com/@user/video/123")
        
        # Assertions
        self.assertIsInstance(result, ImageExtractionResponse)
        self.assertEqual(result.platform, 'tiktok')
        self.assertGreater(len(result.images), 0)
        self.assertEqual(result.metadata['caption'], 'Test slideshow')
        self.assertEqual(result.metadata['author'], 'testuser')
    
    @patch('tools.image.extractors.tiktok.yt_dlp.YoutubeDL')
    @patch('tools.image.extractors.tiktok.requests.get')
    def test_entries_extraction(self, mock_requests_get, mock_ytdl_class):
        """Test extraction when yt-dlp returns entries."""
        # Mock yt-dlp response with entries
        mock_ytdl = MagicMock()
        mock_info = {
            'entries': [
                {'thumbnails': [{'url': 'https://example.com/img1.jpg'}]},
                {'thumbnails': [{'url': 'https://example.com/img2.jpg'}]}
            ],
            'description': 'Multi-image post',
            'uploader': 'testuser'
        }
        mock_ytdl.extract_info.return_value = mock_info
        mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl
        
        # Mock image download
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        
        # Extract
        result = self.extractor.extract("https://www.tiktok.com/@user/video/456")
        
        # Assertions
        self.assertEqual(len(result.images), 2)
        self.assertEqual(len(result.image_urls), 2)
    
    @patch('tools.image.extractors.tiktok.yt_dlp.YoutubeDL')
    def test_no_images_found(self, mock_ytdl_class):
        """Test error handling when no images are found."""
        # Mock yt-dlp response with no thumbnails
        mock_ytdl = MagicMock()
        mock_info = {'description': 'No images'}
        mock_ytdl.extract_info.return_value = mock_info
        mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl
        
        # Extract should raise error
        with self.assertRaises(ImageExtractionError):
            self.extractor.extract("https://www.tiktok.com/@user/video/789")
    
    @patch('tools.image.extractors.tiktok.yt_dlp.YoutubeDL')
    def test_proxy_configuration(self, mock_ytdl_class):
        """Test that proxy is configured in yt-dlp options."""
        mock_ytdl = MagicMock()
        mock_ytdl.extract_info.side_effect = Exception("Stop execution")
        mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl
        
        try:
            self.extractor.extract("https://www.tiktok.com/@user/video/999")
        except:
            pass
        
        # Verify YoutubeDL was called with proxy in options
        call_args = mock_ytdl_class.call_args[0][0]
        self.assertIn('proxy', call_args)
        self.assertEqual(call_args['proxy'], "http://proxy:8080")


if __name__ == '__main__':
    unittest.main()
