"""
Mock tests for scraper service.

Tests the scraper service with mocked extractors to avoid network calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agent.src.tools.scraper import (
    ScraperService,
    ScraperRequest,
    ScraperResponse,
    ContentType,
    ExtractionStrategy,
    PrivateVideoError,
    ExpiredVideoError,
)


class TestScraperService:
    """Test ScraperService with mocked extractors."""
    
    @pytest.fixture
    def service(self):
        """Create a scraper service instance."""
        with patch('agent.src.tools.scraper.service.ProxyManager'):
            return ScraperService()
    
    def test_scrape_youtube_url(self, service):
        """Test scraping a YouTube URL routes to yt-dlp extractor."""
        # Mock the yt-dlp extractor
        mock_response = ScraperResponse(
            title="Test Video",
            description="Test description",
            author="Test Channel",
            content_type=ContentType.VIDEO,
            platform="youtube",
            extraction_strategy=ExtractionStrategy.YTDLP,
            thumbnail_url="https://example.com/thumb.jpg",
            duration=120,
            raw_url="https://www.youtube.com/watch?v=test"
        )
        service.ytdlp_extractor.extract = Mock(return_value=mock_response)
        
        # Test
        request = ScraperRequest(url="https://www.youtube.com/watch?v=test")
        response = service.scrape(request)
        
        # Assertions
        assert response.platform == "youtube"
        assert response.extraction_strategy == ExtractionStrategy.YTDLP
        assert response.title == "Test Video"
        service.ytdlp_extractor.extract.assert_called_once()
    
    def test_scrape_instagram_url(self, service):
        """Test scraping an Instagram URL routes to yt-dlp extractor."""
        mock_response = ScraperResponse(
            title="Instagram Post",
            content_type=ContentType.VIDEO,
            platform="instagram",
            extraction_strategy=ExtractionStrategy.YTDLP,
            raw_url="https://instagram.com/p/test123"
        )
        service.ytdlp_extractor.extract = Mock(return_value=mock_response)
        
        request = ScraperRequest(url="https://instagram.com/p/test123")
        response = service.scrape(request)
        
        assert response.platform == "instagram"
        assert response.extraction_strategy == ExtractionStrategy.YTDLP
    
    def test_scrape_generic_url(self, service):
        """Test scraping a generic URL routes to OpenGraph extractor."""
        mock_response = ScraperResponse(
            title="Generic Page",
            description="Page description",
            content_type=ContentType.LINK,
            platform="generic",
            extraction_strategy=ExtractionStrategy.OPENGRAPH,
            raw_url="https://example.com/page"
        )
        service.opengraph_extractor.extract = Mock(return_value=mock_response)
        
        request = ScraperRequest(url="https://example.com/page")
        response = service.scrape(request)
        
        assert response.platform == "generic"
        assert response.extraction_strategy == ExtractionStrategy.OPENGRAPH
        service.opengraph_extractor.extract.assert_called_once()
    
    def test_scrape_blog_url(self, service):
        """Test scraping a blog URL routes to passthrough handler."""
        mock_response = ScraperResponse(
            description="Text content from medium.com - full extraction pending",
            content_type=ContentType.ARTICLE,
            platform="blog",
            extraction_strategy=ExtractionStrategy.PASSTHROUGH,
            raw_url="https://medium.com/@user/article"
        )
        service.passthrough_handler.extract = Mock(return_value=mock_response)
        
        request = ScraperRequest(url="https://medium.com/@user/article")
        response = service.scrape(request)
        
        assert response.platform == "blog"
        assert response.extraction_strategy == ExtractionStrategy.PASSTHROUGH
        assert response.content_type == ContentType.ARTICLE
    
    def test_scrape_with_platform_hint(self, service):
        """Test scraping with platform hint."""
        mock_response = ScraperResponse(
            title="Hinted Video",
            content_type=ContentType.VIDEO,
            platform="youtube",
            extraction_strategy=ExtractionStrategy.YTDLP,
            raw_url="https://youtu.be/test"
        )
        service.ytdlp_extractor.extract = Mock(return_value=mock_response)
        
        request = ScraperRequest(
            url="https://youtu.be/test",
            platform_hint="youtube"
        )
        response = service.scrape(request)
        
        assert response.platform == "youtube"
    
    def test_graceful_degradation_partial_metadata(self, service):
        """Test that service handles partial metadata (AC: 8)."""
        # Mock response with only required fields
        mock_response = ScraperResponse(
            content_type=ContentType.VIDEO,
            platform="youtube",
            extraction_strategy=ExtractionStrategy.YTDLP,
            raw_url="https://www.youtube.com/watch?v=test",
            title="Partial Video",
            # Missing: description, author, thumbnail_url, duration
        )
        service.ytdlp_extractor.extract = Mock(return_value=mock_response)
        
        request = ScraperRequest(url="https://www.youtube.com/watch?v=test")
        response = service.scrape(request)
        
        assert response.title == "Partial Video"
        assert response.description is None
        assert response.author is None


class TestErrorHandling:
    """Test error handling and classification."""
    
    @pytest.fixture
    def service(self):
        """Create a scraper service instance."""
        with patch('agent.src.tools.scraper.service.ProxyManager'):
            return ScraperService()
    
    def test_private_video_error_propagates(self, service):
        """Test that PrivateVideoError is propagated (AC: 7)."""
        service.ytdlp_extractor.extract = Mock(side_effect=PrivateVideoError("Video is private"))
        
        request = ScraperRequest(url="https://www.youtube.com/watch?v=private")
        
        with pytest.raises(PrivateVideoError):
            service.scrape(request)
    
    def test_expired_video_error_propagates(self, service):
        """Test that ExpiredVideoError is propagated (AC: 7)."""
        service.ytdlp_extractor.extract = Mock(side_effect=ExpiredVideoError("Video deleted"))
        
        request = ScraperRequest(url="https://www.youtube.com/watch?v=deleted")
        
        with pytest.raises(ExpiredVideoError):
            service.scrape(request)


class TestRetryLogic:
    """Test retry logic with exponential backoff (AC: 9)."""
    
    @pytest.fixture
    def service(self):
        """Create a scraper service instance."""
        with patch('agent.src.tools.scraper.service.ProxyManager'):
            return ScraperService()
    
    def test_retry_on_transient_failure(self, service):
        """Test that service retries on transient failures."""
        from agent.src.tools.scraper.types import ScraperError
        
        # Mock extractor to fail twice, then succeed
        mock_response = ScraperResponse(
            title="Success after retry",
            content_type=ContentType.VIDEO,
            platform="youtube",
            extraction_strategy=ExtractionStrategy.YTDLP,
            raw_url="https://www.youtube.com/watch?v=test"
        )
        
        service.ytdlp_extractor.extract = Mock(
            side_effect=[
                ScraperError("Transient error 1"),
                ScraperError("Transient error 2"),
                mock_response
            ]
        )
        
        request = ScraperRequest(url="https://www.youtube.com/watch?v=test")
        response = service.scrape(request)
        
        # Should succeed after retries
        assert response.title == "Success after retry"
        assert service.ytdlp_extractor.extract.call_count == 3
