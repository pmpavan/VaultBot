import logging
import trafilatura
import requests
from typing import Optional

from ..types import ArticleExtractionResponse, ArticleExtractionError, ProxyError
from .base import BaseArticleExtractor
from .opengraph_parser import OpenGraphParser
from ...scraper.proxy.manager import ProxyManager

logger = logging.getLogger(__name__)

class TrafilaturaExtractor(BaseArticleExtractor):
    """Primary article extractor using Trafilatura."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.og_parser = OpenGraphParser()
        
    def extract(self, url: str, html_content: Optional[str] = None) -> ArticleExtractionResponse:
        """
        Extract article using Trafilatura.
        """
        logger.info(f"Extracting article with Trafilatura: {url}")
        
        try:
            downloaded = html_content
            
            # If no HTML provided, fetching it
            if not downloaded:
                proxies = {}
                proxy_url = self.proxy_manager.get_proxy_url()
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}
                
                try:
                    response = requests.get(url, proxies=proxies, timeout=30, verify=False)
                    response.raise_for_status()
                    downloaded = response.text
                except requests.RequestException as e:
                    logger.error(f"Download failed for {url}: {e}")
                    raise ProxyError(f"Failed to download article: {e}")

            if not downloaded:
                raise ArticleExtractionError("Empty content downloaded")

            # Extract main text
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            
            if not text:
                logger.warning(f"Trafilatura failed to extract text for {url}")
                raise ArticleExtractionError("No text extracted")
            
            # Extract metadata
            metadata_json = trafilatura.extract_metadata(downloaded)
            
            # Parse OG tags
            og_tags = self.og_parser.parse(downloaded)
            
            # Construct response
            response = ArticleExtractionResponse(
                text=text,
                url=url,
                title=metadata_json.title if metadata_json else og_tags.get('og:title'),
                author=metadata_json.author if metadata_json else og_tags.get('author'),
                publish_date=metadata_json.date if metadata_json else og_tags.get('article:published_time'),
                site_name=metadata_json.sitename if metadata_json else og_tags.get('og:site_name'),
                og_tags=og_tags,
                metadata=metadata_json.as_dict() if metadata_json else {},
                # Basic classification, refined later
                content_type='article' 
            )
            
            return response
            
        except ArticleExtractionError:
            raise
        except Exception as e:
            logger.error(f"Trafilatura extraction failure: {e}", exc_info=True)
            raise ArticleExtractionError(f"Trafilatura error: {e}")
