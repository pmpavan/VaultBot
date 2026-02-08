import logging
import instaloader
from io import BytesIO
import requests
from typing import Optional, List, Dict

from .base import BaseExtractor
from ..types import ImageExtractionResponse, ImageExtractionError, ProxyError, UnsupportedPlatformError
from tools.scraper.proxy.manager import ProxyManager

logger = logging.getLogger(__name__)

class InstagramExtractor(BaseExtractor):
    """Instagram image extractor using Instaloader."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False
        )
        
    def _configure_proxy(self):
        """Configure proxy for Instaloader."""
        proxy_url = self.proxy_manager.get_proxy_url()
        if proxy_url:
            self.loader.context.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info("Instagram extractor using proxy")

    def extract(self, url: str) -> ImageExtractionResponse:
        """Extract images from Instagram post."""
        self._configure_proxy()
        
        shortcode = self._extract_shortcode(url)
        if not shortcode:
            raise ImageExtractionError(f"Could not extract shortcode from URL: {url}")
            
        try:
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            images = []
            image_urls = []
            
            # handle carousel (sidecars) vs single image
            if post.typename == 'GraphSidecar':
                for node in post.get_sidecar_nodes():
                    if not node.is_video:
                        image_urls.append(node.display_url)
            elif not post.is_video:
                image_urls.append(post.url)
            
            if not image_urls:
                 # It might be a video post, but maybe we can get a thumbnail? 
                 # Story says "image post extraction", but fallback to thumbnail if video? 
                 # Acceptance criteria says "download the image(s)". 
                 # If it's a video, we probably shouldn't be using this extractor, 
                 # or we should extract the thumbnail. 
                 # For now, if no images found, raise error or return empty.
                 # Let's extract thumbnail if it's a video but we were asked to extract images?
                 # Actually, usually 2.4 is for Image Posts. 
                 # If it's a video, 2.9 (Video Post Extraction) handles it.
                 # But if the URL is ambiguous, we might have routed here.
                 if post.is_video:
                     image_urls.append(post.display_url) # Use thumbnail/display url

            # Download images
            for img_url in image_urls:
                try:
                    # Use the same proxy context for downloading
                    resp = requests.get(
                        img_url, 
                        proxies=self.loader.context.proxies,
                        timeout=30
                    )
                    resp.raise_for_status()
                    images.append(resp.content)
                except Exception as e:
                    logger.warning(f"Failed to download image {img_url}: {e}")
            
            if not images:
                raise ImageExtractionError("No images could be downloaded from post")

            return ImageExtractionResponse(
                images=images,
                metadata={
                    'caption': post.caption,
                    'author': post.owner_username,
                    'likes': post.likes,
                    'date': post.date_utc.isoformat() if post.date_utc else None,
                    'hashtags': post.caption_hashtags
                },
                platform='instagram',
                image_urls=image_urls
            )
            
        except instaloader.ConnectionException as e:
             # This often indicates proxy issues or rate limits
             raise ProxyError(f"Instagram connection failed: {e}")
        except instaloader.QueryReturnedNotFoundException:
             raise ImageExtractionError("Instagram post not found")
        except instaloader.LoginRequiredException:
             raise ImageExtractionError("Instagram login required (public access blocked)")
        except Exception as e:
            raise ImageExtractionError(f"Instagram extraction failed: {e}")

    def _extract_shortcode(self, url: str) -> Optional[str]:
        """Extract shortcode from Instagram URL."""
        # primitive regex or check
        import re
        match = re.search(r'(?:/p/|/reel/|/tv/)([\w-]+)', url)
        return match.group(1) if match else None
