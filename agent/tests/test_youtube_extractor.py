import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tools.image.extractors.youtube import YouTubeCommunityExtractor
from tools.image.types import ImageExtractionResponse, ImageExtractionError


class TestYouTubeCommunityExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = YouTubeCommunityExtractor()
        self.extractor.proxy_manager = MagicMock()
        self.extractor.proxy_manager.get_proxy_url.return_value = "http://proxy:8080"
    
    @patch('tools.image.extractors.youtube.requests.get')
    def test_og_image_extraction(self, mock_requests_get):
        """Test extraction using Open Graph meta tags."""
        # Mock HTML response
        html_content = """
        <html>
            <head>
                <meta property="og:image" content="https://example.com/community-image.jpg" />
                <title>YouTube Community Post</title>
            </head>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_requests_get.return_value = mock_response
        
        # Extract
        result = self.extractor.extract("https://www.youtube.com/post/Ugkx123")
        
        # Assertions
        self.assertIsInstance(result, ImageExtractionResponse)
        self.assertEqual(result.platform, 'youtube')
        self.assertGreater(len(result.images), 0)
        self.assertIn('https://example.com/community-image.jpg', result.image_urls)
    
    @patch('tools.image.extractors.youtube.requests.get')
    def test_json_ld_extraction(self, mock_requests_get):
        """Test extraction using JSON-LD structured data."""
        # Mock HTML with JSON-LD
        html_content = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "image": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
                }
                </script>
                <title>YouTube Post</title>
            </head>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_requests_get.return_value = mock_response
        
        # Extract
        result = self.extractor.extract("https://www.youtube.com/post/Ugkx456")
        
        # Assertions
        self.assertEqual(len(result.image_urls), 2)
    
    @patch('tools.image.extractors.youtube.requests.get')
    def test_no_images_found(self, mock_requests_get):
        """Test error handling when no images are detected."""
        # Mock HTML without images
        html_content = """
        <html>
            <head><title>YouTube Post</title></head>
            <body>No images here</body>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        
        # Extract should raise error
        with self.assertRaises(ImageExtractionError) as context:
            self.extractor.extract("https://www.youtube.com/post/Ugkx789")
        
        self.assertIn("Could not detect images", str(context.exception))
    
    @patch('tools.image.extractors.youtube.requests.get')
    def test_proxy_usage(self, mock_requests_get):
        """Test that proxy is used in requests."""
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status.side_effect = Exception("Stop")
        mock_requests_get.return_value = mock_response
        
        try:
            self.extractor.extract("https://www.youtube.com/post/Ugkx999")
        except:
            pass
        
        # Verify requests.get was called with proxies
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('proxies', call_kwargs)
        self.assertEqual(call_kwargs['proxies']['http'], "http://proxy:8080")
    
    @patch('tools.image.extractors.youtube.requests.get')
    def test_request_headers(self, mock_requests_get):
        """Test that proper browser headers are sent."""
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status.side_effect = Exception("Stop")
        mock_requests_get.return_value = mock_response
        
        try:
            self.extractor.extract("https://www.youtube.com/post/UgkxAAA")
        except:
            pass
        
        # Verify headers
        call_kwargs = mock_requests_get.call_args[1]
        self.assertIn('headers', call_kwargs)
        self.assertIn('User-Agent', call_kwargs['headers'])


if __name__ == '__main__':
    unittest.main()
