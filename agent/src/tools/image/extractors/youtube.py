from .base import BaseExtractor
from ..types import ImageExtractionResponse, ImageExtractionError
from tools.scraper.proxy.manager import ProxyManager
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class YouTubeCommunityExtractor(BaseExtractor):
    """YouTube Community Post image extractor."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
    
    def extract(self, url: str) -> ImageExtractionResponse:
        """Extract images from YouTube Community Post."""
        # Note: YouTube Community posts are difficult to scrape as they are dynamic.
        # This is a best-effort implementation using basic HTML parsing.
        # A headless browser would be better but is not available in this environment.
        
        # Configure proxy
        proxy_url = self.proxy_manager.get_proxy_url()
        proxies = None
        if proxy_url:
            proxies = {'http': proxy_url, 'https': proxy_url}
            logger.info("YouTube extractor using proxy")
        
        try:
            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # YouTube's HTML is heavily obfuscated and dynamic (polymer).
            # Basic requests often return the initial skeleton.
            # We look for meta tags or script data.
            
            images = []
            image_urls = []
            
            # Try to find OG image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_urls.append(og_image['content'])
                
            # Try to find structured data (JSON-LD)
            import json
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if 'image' in data:
                        if isinstance(data['image'], list):
                             image_urls.extend(data['image'])
                        elif isinstance(data['image'], str):
                             image_urls.append(data['image'])
                except:
                    continue

            if not image_urls:
                # If we can't find specific post images, we fallback to raising error
                # because returning the channel avatar (often og:image) is misleading.
                raise ImageExtractionError("Could not detect images in YouTube Community Post (dynamic content)")
            
            # Download matched images
            for img_url in image_urls:
                 try:
                    r = requests.get(img_url, proxies=proxies, timeout=30)
                    if r.status_code == 200:
                        images.append(r.content)
                 except Exception as e:
                     logger.warning(f"Failed to download YouTube image {img_url}: {e}")

            if not images:
                raise ImageExtractionError("Failed to download detected images")

            return ImageExtractionResponse(
                images=images,
                metadata={
                    'title': soup.title.string if soup.title else 'YouTube Post',
                    'original_url': url,
                    'platform': 'youtube'
                },
                platform='youtube',
                image_urls=image_urls
            )

        except Exception as e:
            raise ImageExtractionError(f"YouTube extraction failed: {e}")
