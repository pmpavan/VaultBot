from .base import BaseExtractor
from ..types import ImageExtractionResponse, ImageExtractionError
from tools.scraper.proxy.manager import ProxyManager
import logging

logger = logging.getLogger(__name__)

class TikTokExtractor(BaseExtractor):
    """TikTok image carousel extractor."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
    
    def extract(self, url: str) -> ImageExtractionResponse:
        """Extract images from TikTok video/slideshow URL."""
        import yt_dlp
        import requests
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,
        }
        
        # Configure proxy for yt-dlp
        proxy_url = self.proxy_manager.get_proxy_url()
        if proxy_url:
            ydl_opts['proxy'] = proxy_url
            logger.info("TikTok extractor using proxy")
        
        # Prepare proxy dict for requests
        proxies = None
        if proxy_url:
            proxies = {'http': proxy_url, 'https': proxy_url}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check for images in 'thumbnails' or specific formats
                # TikTok slideshows often expose images as thumbnails
                images = []
                image_urls = []
                
                # Strategy 1: Check for 'thumbnails' (often contains the images for slideshows)
                # Note: This is an approximation. Real slideshow scraping is complex.
                if 'thumbnails' in info and info['thumbnails']:
                    # Get the largest thumbnail as a proxy for the image content if it's a single video
                    # For slideshows, yt-dlp might return entries
                    best_thumb = info['thumbnails'][-1]['url']
                    image_urls.append(best_thumb)
                
                # Strategy 2: Check for 'entries' if it's a playlist/slideshow
                if 'entries' in info:
                    for entry in info['entries']:
                         if 'thumbnails' in entry:
                             best_thumb = entry['thumbnails'][-1]['url']
                             image_urls.append(best_thumb)
                             
                if not image_urls:
                    raise ImageExtractionError("No images found in TikTok URL")
                
                # Download images
                for img_url in image_urls:
                    try:
                        resp = requests.get(img_url, proxies=proxies, timeout=30)
                        resp.raise_for_status()
                        images.append(resp.content)
                    except Exception as e:
                        logger.warning(f"Failed to download TikTok image {img_url}: {e}")
                        # Continue to next image
                
                if not images:
                    raise ImageExtractionError("Failed to download any images from TikTok")

                return ImageExtractionResponse(
                    images=images,
                    metadata={
                        'caption': info.get('description') or info.get('title'),
                        'author': info.get('uploader'),
                        'date': info.get('upload_date'),
                        'platform_id': info.get('id')
                    },
                    platform='tiktok',
                    image_urls=image_urls
                )
                
        except Exception as e:
            raise ImageExtractionError(f"TikTok extraction failed: {e}")
