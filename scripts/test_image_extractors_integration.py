#!/usr/bin/env python3
"""
Integration test script for image extractors.
Tests real extraction with sample URLs (requires network access).

Usage:
    python scripts/test_image_extractors_integration.py
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../agent/src'))

from tools.image.service import ImageExtractorService
from tools.image.types import ImageExtractionRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_instagram():
    """Test Instagram extraction with a sample public post."""
    logger.info("Testing Instagram extraction...")
    
    service = ImageExtractorService()
    
    # Use a well-known public Instagram post (adjust URL as needed)
    # Note: This requires the post to be public and accessible
    test_url = "https://www.instagram.com/p/C1234567890/"  # Replace with actual public post
    
    try:
        request = ImageExtractionRequest(url=test_url)
        result = service.extract(request)
        
        logger.info(f"✅ Instagram extraction successful")
        logger.info(f"   Platform: {result.platform}")
        logger.info(f"   Images: {len(result.images)}")
        logger.info(f"   Metadata: {result.metadata}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Instagram extraction failed: {e}")
        return False


def test_tiktok():
    """Test TikTok extraction with a sample public video/slideshow."""
    logger.info("Testing TikTok extraction...")
    
    service = ImageExtractorService()
    
    # Use a well-known public TikTok post
    test_url = "https://www.tiktok.com/@user/video/1234567890"  # Replace with actual public post
    
    try:
        request = ImageExtractionRequest(url=test_url)
        result = service.extract(request)
        
        logger.info(f"✅ TikTok extraction successful")
        logger.info(f"   Platform: {result.platform}")
        logger.info(f"   Images: {len(result.images)}")
        logger.info(f"   Metadata: {result.metadata}")
        
        return True
    except Exception as e:
        logger.error(f"❌ TikTok extraction failed: {e}")
        return False


def test_youtube():
    """Test YouTube Community Post extraction."""
    logger.info("Testing YouTube extraction...")
    
    service = ImageExtractorService()
    
    # Use a well-known public YouTube community post
    test_url = "https://www.youtube.com/post/UgkxABC123"  # Replace with actual public post
    
    try:
        request = ImageExtractionRequest(url=test_url)
        result = service.extract(request)
        
        logger.info(f"✅ YouTube extraction successful")
        logger.info(f"   Platform: {result.platform}")
        logger.info(f"   Images: {len(result.images)}")
        logger.info(f"   Metadata: {result.metadata}")
        
        return True
    except Exception as e:
        logger.error(f"❌ YouTube extraction failed: {e}")
        return False


def main():
    """Run all integration tests."""
    logger.info("=" * 60)
    logger.info("Image Extractor Integration Tests")
    logger.info("=" * 60)
    logger.info("")
    logger.info("⚠️  NOTE: These tests require network access and valid public URLs.")
    logger.info("⚠️  Update the test URLs in this script before running.")
    logger.info("")
    
    results = {
        'Instagram': test_instagram(),
        'TikTok': test_tiktok(),
        'YouTube': test_youtube()
    }
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    for platform, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{platform}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    logger.info("")
    logger.info(f"Total: {total_passed}/{total_tests} tests passed")
    
    return 0 if total_passed == total_tests else 1


if __name__ == '__main__':
    sys.exit(main())
