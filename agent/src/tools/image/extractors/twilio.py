import logging
from typing import List
from .base import BaseExtractor
from ..types import ImageExtractionResponse, ImageExtractionError
from ..downloader import ImageDownloader

logger = logging.getLogger(__name__)

class TwilioExtractor(BaseExtractor):
    """Extractor for Twilio/WhatsApp media URLs."""

    def __init__(self):
        self.downloader = ImageDownloader()

    def extract(self, url: str) -> ImageExtractionResponse:
        """
        Extract image from a Twilio Media URL.
        
        Args:
            url: The Twilio Media URL.
            
        Returns:
            ImageExtractionResponse containing the image bytes and metadata.
        """
        try:
            logger.info(f"Extracting image from Twilio URL: {url}")
            
            # Download the image
            image_bytes = self.downloader.download(url)
            
            return ImageExtractionResponse(
                images=[image_bytes],
                metadata={
                    "platform": "twilio",
                    "caption": "WhatsApp Image",
                    "source": "twilio"
                },
                platform="twilio",
                image_urls=[url]
            )
        except Exception as e:
            logger.error(f"Twilio extraction failed for {url}: {e}")
            raise ImageExtractionError(f"Twilio extraction failed: {str(e)}")
