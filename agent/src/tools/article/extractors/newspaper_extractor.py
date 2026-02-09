import logging
import newspaper
from typing import Optional
from newspaper import Article

from ..types import ArticleExtractionResponse, ArticleExtractionError
from .base import BaseArticleExtractor
from .opengraph_parser import OpenGraphParser
from ...scraper.proxy.manager import ProxyManager

logger = logging.getLogger(__name__)

class NewspaperExtractor(BaseArticleExtractor):
    """Fallback article extractor using Newspaper4k."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.og_parser = OpenGraphParser()
        
    def extract(self, url: str, html_content: Optional[str] = None) -> ArticleExtractionResponse:
        """
        Extract article using Newspaper4k.
        """
        logger.info(f"Extracting article with Newspaper4k: {url}")
        
        try:
            config = newspaper.Config()
            config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            
            # Use proxy if configured
            proxy_url = self.proxy_manager.get_proxy_url()
            if proxy_url:
                config.proxies = {'http': proxy_url, 'https': proxy_url}
            
            article = Article(url, config=config)
            
            if html_content:
                article.set_html(html_content)
                article.parse()
            else:
                article.download()
                article.parse()
                
            if not article.text:
                raise ArticleExtractionError("No text extracted by Newspaper4k")
            
            # Parse OG tags from the HTML
            og_tags = self.og_parser.parse(article.html)
            
            # Construct response
            response = ArticleExtractionResponse(
                text=article.text,
                url=url,
                title=article.title or og_tags.get('og:title'),
                author=', '.join(article.authors) if article.authors else og_tags.get('author'),
                publish_date=str(article.publish_date) if article.publish_date else og_tags.get('article:published_time'),
                site_name=og_tags.get('og:site_name'),
                og_tags=og_tags,
                metadata={
                    'keywords': article.keywords,
                    'summary': article.summary,
                    'top_image': article.top_image
                },
                content_type='article'
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Newspaper4k extraction failure: {e}", exc_info=True)
            raise ArticleExtractionError(f"Newspaper4k error: {e}")
