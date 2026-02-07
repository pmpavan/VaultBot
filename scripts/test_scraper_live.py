"""
Live integration test script for scraper service.

Tests with real URLs to verify end-to-end functionality.
Run manually: python3 scripts/test_scraper_live.py
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.src.tools.scraper import ScraperService, ScraperRequest

# Load environment variables
load_dotenv()


def test_youtube_url():
    """Test scraping a YouTube URL."""
    print("\n=== Testing YouTube URL ===")
    service = ScraperService()
    request = ScraperRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    
    try:
        response = service.scrape(request)
        print(f"✅ Success!")
        print(f"Title: {response.title}")
        print(f"Author: {response.author}")
        print(f"Platform: {response.platform}")
        print(f"Strategy: {response.extraction_strategy}")
        print(f"Duration: {response.duration}s")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_instagram_url():
    """Test scraping an Instagram URL."""
    print("\n=== Testing Instagram URL ===")
    service = ScraperService()
    # Note: Use a real Instagram URL for testing
    request = ScraperRequest(url="https://www.instagram.com/p/example/")
    
    try:
        response = service.scrape(request)
        print(f"✅ Success!")
        print(f"Title: {response.title}")
        print(f"Platform: {response.platform}")
        print(f"Strategy: {response.extraction_strategy}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_generic_url():
    """Test scraping a generic URL with OpenGraph."""
    print("\n=== Testing Generic URL (OpenGraph) ===")
    service = ScraperService()
    request = ScraperRequest(url="https://github.com/yt-dlp/yt-dlp")
    
    try:
        response = service.scrape(request)
        print(f"✅ Success!")
        print(f"Title: {response.title}")
        print(f"Description: {response.description[:100]}..." if response.description else "None")
        print(f"Platform: {response.platform}")
        print(f"Strategy: {response.extraction_strategy}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_blog_url():
    """Test scraping a blog URL (passthrough)."""
    print("\n=== Testing Blog URL (Passthrough) ===")
    service = ScraperService()
    request = ScraperRequest(url="https://medium.com/@example/article")
    
    try:
        response = service.scrape(request)
        print(f"✅ Success!")
        print(f"Description: {response.description}")
        print(f"Platform: {response.platform}")
        print(f"Strategy: {response.extraction_strategy}")
        print(f"Content Type: {response.content_type}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🚀 Starting Scraper Service Live Tests")
    print("=" * 50)
    
    test_youtube_url()
    test_generic_url()
    test_blog_url()
    # test_instagram_url()  # Uncomment with real URL
    
    print("\n" + "=" * 50)
    print("✅ Live tests completed")
