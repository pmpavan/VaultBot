import unittest
from unittest.mock import MagicMock, patch, Mock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tools.image.extractors.instagram import InstagramExtractor
from tools.image.types import ImageExtractionResponse, ImageExtractionError, ProxyError


class TestInstagramExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = InstagramExtractor()
        self.extractor.proxy_manager = MagicMock()
        self.extractor.proxy_manager.get_proxy_url.return_value = "http://proxy:8080"
    
    def test_shortcode_extraction(self):
        """Test shortcode extraction from various Instagram URL formats."""
        test_cases = [
            ("https://www.instagram.com/p/ABC123/", "ABC123"),
            ("https://instagram.com/reel/XYZ789/", "XYZ789"),
            ("https://www.instagram.com/tv/DEF456/", "DEF456"),
        ]
        
        for url, expected_shortcode in test_cases:
            shortcode = self.extractor._extract_shortcode(url)
            self.assertEqual(shortcode, expected_shortcode)
    
    def test_shortcode_extraction_invalid(self):
        """Test shortcode extraction with invalid URLs."""
        invalid_url = "https://www.instagram.com/user/"
        shortcode = self.extractor._extract_shortcode(invalid_url)
        self.assertIsNone(shortcode)
    
    @patch('tools.image.extractors.instagram.instaloader.Post')
    @patch('tools.image.extractors.instagram.requests.get')
    def test_single_image_extraction(self, mock_requests_get, mock_post_class):
        """Test extraction of a single image post."""
        # Mock post
        mock_post = MagicMock()
        mock_post.typename = 'GraphImage'
        mock_post.is_video = False
        mock_post.url = "https://example.com/image.jpg"
        mock_post.caption = "Test caption"
        mock_post.owner_username = "testuser"
        mock_post.likes = 100
        mock_post.date_utc = None
        mock_post.caption_hashtags = ["test"]
        
        mock_post_class.from_shortcode.return_value = mock_post
        
        # Mock image download
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        
        # Extract
        result = self.extractor.extract("https://www.instagram.com/p/ABC123/")
        
        # Assertions
        self.assertIsInstance(result, ImageExtractionResponse)
        self.assertEqual(result.platform, 'instagram')
        self.assertEqual(len(result.images), 1)
        self.assertEqual(result.images[0], b"fake_image_data")
        self.assertEqual(result.metadata['caption'], "Test caption")
        self.assertEqual(result.metadata['author'], "testuser")
    
    @patch('tools.image.extractors.instagram.instaloader.Post')
    @patch('tools.image.extractors.instagram.requests.get')
    def test_carousel_extraction(self, mock_requests_get, mock_post_class):
        """Test extraction of a carousel post with multiple images."""
        # Mock carousel post
        mock_post = MagicMock()
        mock_post.typename = 'GraphSidecar'
        mock_post.is_video = False
        mock_post.caption = "Carousel test"
        mock_post.owner_username = "testuser"
        mock_post.likes = 200
        mock_post.date_utc = None
        mock_post.caption_hashtags = []
        
        # Mock sidecar nodes
        mock_node1 = MagicMock()
        mock_node1.is_video = False
        mock_node1.display_url = "https://example.com/img1.jpg"
        
        mock_node2 = MagicMock()
        mock_node2.is_video = False
        mock_node2.display_url = "https://example.com/img2.jpg"
        
        mock_post.get_sidecar_nodes.return_value = [mock_node1, mock_node2]
        mock_post_class.from_shortcode.return_value = mock_post
        
        # Mock image downloads
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        
        # Extract
        result = self.extractor.extract("https://www.instagram.com/p/CAROUSEL/")
        
        # Assertions
        self.assertEqual(len(result.images), 2)
        self.assertEqual(len(result.image_urls), 2)
    
    @patch('tools.image.extractors.instagram.instaloader.Post')
    def test_proxy_rotation_on_failure(self, mock_post_class):
        """Test that proxy rotation occurs on connection failures."""
        # Simulate connection failure
        mock_post_class.from_shortcode.side_effect = Exception("Connection failed")
        
        # Extract should retry and eventually raise ProxyError
        with self.assertRaises(ProxyError):
            self.extractor.extract("https://www.instagram.com/p/FAIL/")
        
        # Verify proxy rotation was called
        self.assertGreater(self.extractor.proxy_manager.rotate_proxy.call_count, 0)


if __name__ == '__main__':
    unittest.main()
