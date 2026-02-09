"""
Integration test for Article Extraction Service.
Run with: python scripts/test_article_extraction_integration.py
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../agent/src'))
print(sys.path)

from tools.article.service import ArticleService
from tools.article.types import ArticleExtractionRequest

# Configure logging to see info
logging.basicConfig(level=logging.INFO)

def test_extraction():
    service = ArticleService()
    
    test_urls = [
        # News
        "https://www.bbc.com/news/technology-68139414", 
        # Tech Blog
        "https://simonwillison.net/2024/Feb/5/accidental-prompt-injection/",
        # Python Documentation
        "https://docs.python.org/3/library/asyncio.html",
        # Wikipedia (Generic)
        "https://en.wikipedia.org/wiki/Artificial_intelligence"
    ]
    
    print("🚀 Starting Article Extraction Integration Test")
    print("==============================================")
    
    for url in test_urls:
        print(f"\nProcessing: {url}")
        try:
            request = ArticleExtractionRequest(url=url)
            response = service.extract(request)
            
            print(f"✅ Success!")
            print(f"Title: {response.title}")
            print(f"Type: {response.content_type}")
            print(f"Author: {response.author}")
            print(f"Date: {response.publish_date}")
            print(f"Text Length: {len(response.text)} chars")
            print(f"OG Tags: {len(response.og_tags)} found")
            print(f"Is Paywall: {response.is_paywall}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_extraction()
