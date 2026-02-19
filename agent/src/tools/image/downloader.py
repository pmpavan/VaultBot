import logging
import httpx
import os
from typing import Optional

logger = logging.getLogger(__name__)

class ImageDownloader:
    """Tool to download image bytes from a URL."""

    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials missing. Media downloads from Twilio may fail.")

    def download(self, url: str) -> bytes:
        """
        Download image bytes from the URL.
        
        Args:
            url: The URL to download from.
            
        Returns:
            The image content as bytes.
            
        Raises:
            Exception: If download fails.
        """
        logger.info(f"Downloading image from {url}")
        
        # Determine if we need auth (for Twilio URLs)
        auth = None
        if 'api.twilio.com' in url and self.account_sid and self.auth_token:
            auth = (self.account_sid, self.auth_token)
            logger.debug("Using Twilio Basic Auth for download")

        try:
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                response = client.get(url, auth=auth)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading image from {url}: {e}")
            raise Exception(f"Failed to download image: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error downloading image from {url}: {e}")
            raise Exception(f"Unexpected error during download: {str(e)}")
