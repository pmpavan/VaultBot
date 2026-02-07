"""
OpenGraph extractor for generic URLs.

Extracts basic metadata from web pages using OpenGraph tags.
Falls back to standard HTML meta tags if OpenGraph is not available.
"""

import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup

from ..types import (
    ScraperResponse,
    ContentType,
    ExtractionStrategy,
    ScraperError,
)

logger = logging.getLogger(__name__)


class OpenGraphExtractor:
    """Extracts metadata using OpenGraph tags."""
    
    def __init__(self, timeout: int = 10, user_agent: str = None):
        """
        Initialize OpenGraph extractor.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Optional custom user agent string
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (compatible; VaultBot/1.0; +https://vaultbot.app)'
        }
    
    def extract(self, url: str) -> ScraperResponse:
        """
        Extract metadata from a generic URL using OpenGraph tags.
        
        Args:
            url: URL to extract metadata from
            
        Returns:
            ScraperResponse with extracted metadata
            
        Raises:
            ScraperError: If extraction fails
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Use lxml parser for better performance
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try OpenGraph tags first
            title = self._get_og_tag(soup, 'og:title') or self._get_title_tag(soup)
            description = self._get_og_tag(soup, 'og:description') or self._get_meta_description(soup)
            image = self._get_og_tag(soup, 'og:image')
            site_name = self._get_og_tag(soup, 'og:site_name')
            
            return ScraperResponse(
                title=title,
                description=description,
                author=site_name,  # Use site name as author
                content_type=ContentType.LINK,
                platform='generic',
                extraction_strategy=ExtractionStrategy.OPENGRAPH,
                thumbnail_url=image,
                raw_url=url,
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise ScraperError(f"Failed to fetch URL: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting {url}: {e}")
            raise ScraperError(f"Unexpected error: {e}")
    
    def _get_og_tag(self, soup: BeautifulSoup, property_name: str) -> Optional[str]:
        """Extract OpenGraph tag value."""
        tag = soup.find('meta', property=property_name)
        return tag.get('content') if tag else None
    
    def _get_title_tag(self, soup: BeautifulSoup) -> Optional[str]:
        """Fallback to <title> tag."""
        title_tag = soup.find('title')
        return title_tag.string if title_tag else None
    
    def _get_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Fallback to <meta name="description"> tag."""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        return meta_tag.get('content') if meta_tag else None
