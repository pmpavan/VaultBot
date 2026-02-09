from typing import Optional
from urllib.parse import urlparse
import re

from .types import ArticleContentType

class ContentClassifier:
    """Classifies content type based on URL and metadata."""
    
    @staticmethod
    def classify(url: str, html: Optional[str] = None, title: Optional[str] = None) -> ArticleContentType:
        """
        Classify content type.
        
        Args:
            url: Content URL
            html: HTML content (optional)
            title: Extracted title (optional)
            
        Returns:
            ArticleContentType: 'article', 'blog', 'documentation', or 'generic'
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Documentation patterns
        if any(d in domain for d in ['docs.', 'readthedoc', 'documentation']):
            return 'documentation'
        if '/docs/' in path or '/documentation/' in path:
            return 'documentation'
            
        # Blog patterns
        if '/blog/' in path or 'blog.' in domain or 'medium.com' in domain:
            return 'blog'
        
        # Article/News patterns (refined)
        if any(d in domain for d in ['news.', 'nytimes.com', 'bbc.com', 'cnn.com', 'reuters.com']):
            return 'article'
        
        # Generic fallback
        return 'generic'
