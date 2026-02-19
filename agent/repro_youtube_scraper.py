
import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

# Force fallback to yt-dlp by unsetting API key
if 'YOUTUBE_API_KEY' in os.environ:
    del os.environ['YOUTUBE_API_KEY']
    logger.info("Unset YOUTUBE_API_KEY to test fallback")

from tools.scraper.service import ScraperService
from tools.scraper.types import ScraperRequest

def test_youtube_scraping():
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # Me at the zoo
    
    logger.info(f"Testing YouTube scraping for {url}")
    
    scraper = ScraperService()
    
    try:
        request = ScraperRequest(url=url)
        result = scraper.scrape(request)
        
        print("\nSUCCESS!")
        print(f"Title: {result.title}")
        print(f"Author: {result.author}")
        print(f"Duration: {result.duration}")
        print(f"Strategy: {result.extraction_strategy}")
        print(f"Platform: {result.platform}")
        
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_youtube_scraping()
