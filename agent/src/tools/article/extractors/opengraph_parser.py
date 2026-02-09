from typing import Dict, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class OpenGraphParser:
    """Parses OpenGraph and standard metadata from HTML."""
    
    @staticmethod
    def parse(html: str) -> Dict[str, str]:
        """
        Extract OpenGraph and other meta tags from HTML.
        
        Args:
            html: HTML content string.
            
        Returns:
            Dictionary of extracted tags (e.g., {'og:title': '...', 'description': '...'}).
        """
        if not html:
            return {}
            
        try:
            soup = BeautifulSoup(html, 'lxml')
            meta_tags = soup.find_all('meta')
            
            extracted = {}
            
            for tag in meta_tags:
                # OpenGraph properties
                if tag.get('property', '').startswith('og:'):
                    extracted[tag['property']] = tag.get('content', '')
                
                # Twitter card properties
                elif tag.get('name', '').startswith('twitter:'):
                    extracted[tag['name']] = tag.get('content', '')
                
                # Standard metadata
                elif tag.get('name') in ['description', 'author', 'keywords', 'pubdate', 'lastmod']:
                    extracted[tag['name']] = tag.get('content', '')
                
                # Article specific metadata
                elif tag.get('property', '').startswith('article:'):
                    extracted[tag['property']] = tag.get('content', '')
                    
            return extracted
            
        except Exception as e:
            logger.warning(f"Failed to parse OpenGraph tags: {e}")
            return {}
