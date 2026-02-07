"""
Proxy manager for handling proxy configuration and health checks.

Manages rotating residential proxies for social media scraping.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy configuration for scrapers."""
    
    def __init__(self):
        """Initialize proxy manager from environment variables."""
        self.provider = os.getenv('PROXY_PROVIDER')
        self.username = os.getenv('PROXY_USERNAME')
        self.password = os.getenv('PROXY_PASSWORD')
        self.host = os.getenv('PROXY_HOST')
        self.port = os.getenv('PROXY_PORT')
        
        self._proxy_url = None
        if all([self.username, self.password, self.host, self.port]):
            self._proxy_url = f"http://{self.username}:{self.password}@{self.host}:{self.port}"
            logger.info(f"Proxy configured: {self.provider} ({self.host}:{self.port})")
        else:
            logger.warning("Proxy not configured - some features may not work")
    
    def get_proxy_url(self) -> Optional[str]:
        """
        Get the configured proxy URL.
        
        Returns:
            Proxy URL in format: http://user:pass@host:port
            None if proxy is not configured
        """
        return self._proxy_url
    
    def is_configured(self) -> bool:
        """Check if proxy is configured."""
        return self._proxy_url is not None
    
    def health_check(self) -> bool:
        """
        Perform a health check on the proxy.
        
        Returns:
            True if proxy is healthy, False otherwise
        """
        if not self.is_configured():
            return False
        
        # Test proxy connectivity with a simple request
        import requests
        
        try:
            # Use a lightweight endpoint for health check
            response = requests.get(
                'https://httpbin.org/ip',
                proxies={'http': self._proxy_url, 'https': self._proxy_url},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Proxy health check failed: {e}")
            return False
