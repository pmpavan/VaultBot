import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tools.image.service import ImageExtractorService
from tools.image.types import ImageExtractionRequest, ImageExtractionResponse, UnsupportedPlatformError

class TestImageExtractorService(unittest.TestCase):
    
    def setUp(self):
        self.service = ImageExtractorService()
        self.service.instagram_extractor = MagicMock()
        self.service.tiktok_extractor = MagicMock()
        self.service.youtube_extractor = MagicMock()
        self.service.twilio_extractor = MagicMock()

    def test_routing_instagram(self):
        request = ImageExtractionRequest(url="https://www.instagram.com/p/C12345/")
        self.service.extract(request)
        self.service.instagram_extractor.extract.assert_called_once_with("https://www.instagram.com/p/C12345/")

    def test_routing_tiktok(self):
        request = ImageExtractionRequest(url="https://www.tiktok.com/@user/video/12345")
        self.service.extract(request)
        self.service.tiktok_extractor.extract.assert_called_once_with("https://www.tiktok.com/@user/video/12345")

    def test_routing_youtube(self):
        request = ImageExtractionRequest(url="https://www.youtube.com/post/Ugkx...")
        self.service.extract(request)
        self.service.youtube_extractor.extract.assert_called_once_with("https://www.youtube.com/post/Ugkx...")

    def test_routing_twilio(self):
        request = ImageExtractionRequest(url="https://api.twilio.com/2010-04-01/Accounts/AC.../Media/ME...")
        self.service.extract(request)
        self.service.twilio_extractor.extract.assert_called_once_with("https://api.twilio.com/2010-04-01/Accounts/AC.../Media/ME...")

    def test_unsupported_platform(self):
        request = ImageExtractionRequest(url="https://example.com/image.jpg")
        with self.assertRaises(UnsupportedPlatformError):
            self.service.extract(request)

if __name__ == '__main__':
    unittest.main()
