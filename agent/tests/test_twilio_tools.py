import unittest
from unittest.mock import MagicMock, patch
import httpx
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tools.image.downloader import ImageDownloader
from tools.image.extractors.twilio import TwilioExtractor
from tools.image.types import ImageExtractionResponse, ImageExtractionError

class TestImageDownloader(unittest.TestCase):
    
    def setUp(self):
        self.downloader = ImageDownloader()

    @patch('httpx.Client.get')
    def test_download_no_auth(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.content = b"fake_image_content"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        url = "https://example.com/image.jpg"
        content = self.downloader.download(url)
        
        self.assertEqual(content, b"fake_image_content")
        # Ensure no auth used for non-twilio URL
        args, kwargs = mock_get.call_args
        self.assertIsNone(kwargs.get('auth'))

    @patch('httpx.Client.get')
    def test_download_with_twilio_auth(self, mock_get):
        # Set env vars for testing
        with patch.dict(os.environ, {'TWILIO_ACCOUNT_SID': 'AC123', 'TWILIO_AUTH_TOKEN': 'secret'}):
            downloader = ImageDownloader()
            
            mock_response = MagicMock()
            mock_response.content = b"twilio_image"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            url = "https://api.twilio.com/2010-04-01/Accounts/AC123/Media/ME123"
            content = downloader.download(url)
            
            self.assertEqual(content, b"twilio_image")
            # Ensure auth was used
            args, kwargs = mock_get.call_args
            self.assertEqual(kwargs.get('auth'), ('AC123', 'secret'))

class TestTwilioExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = TwilioExtractor()

    @patch('tools.image.downloader.ImageDownloader.download')
    def test_extract_success(self, mock_download):
        mock_download.return_value = b"image_bytes"
        
        url = "https://api.twilio.com/media/123"
        response = self.extractor.extract(url)
        
        self.assertIsInstance(response, ImageExtractionResponse)
        self.assertEqual(response.images[0], b"image_bytes")
        self.assertEqual(response.platform, "twilio")
        self.assertEqual(response.metadata["platform"], "twilio")

    @patch('tools.image.downloader.ImageDownloader.download')
    def test_extract_failure(self, mock_download):
        mock_download.side_effect = Exception("Download failed")
        
        url = "https://api.twilio.com/media/123"
        with self.assertRaises(ImageExtractionError):
            self.extractor.extract(url)

if __name__ == '__main__':
    unittest.main()
