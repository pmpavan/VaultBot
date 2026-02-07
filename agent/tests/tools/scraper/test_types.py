"""
Unit tests for scraper data contracts (types.py).

Tests Pydantic models, enums, and custom exceptions.
"""

import pytest
from agent.src.tools.scraper.types import (
    ExtractionStrategy,
    ContentType,
    ScraperRequest,
    ScraperResponse,
    ScraperError,
    PrivateVideoError,
    ExpiredVideoError,
    UnsupportedPlatformError,
    ProxyError,
    GeoRestrictedError,
)


class TestEnums:
    """Test enum definitions."""
    
    def test_extraction_strategy_values(self):
        """Test ExtractionStrategy enum has correct values."""
        assert ExtractionStrategy.YTDLP == "ytdlp"
        assert ExtractionStrategy.OPENGRAPH == "opengraph"
        assert ExtractionStrategy.PASSTHROUGH == "passthrough"
        assert ExtractionStrategy.VISION == "vision"
    
    def test_content_type_values(self):
        """Test ContentType enum has correct values."""
        assert ContentType.VIDEO == "video"
        assert ContentType.IMAGE == "image"
        assert ContentType.ARTICLE == "article"
        assert ContentType.LINK == "link"


class TestScraperRequest:
    """Test ScraperRequest Pydantic model."""
    
    def test_valid_request_with_hint(self):
        """Test creating a valid request with platform hint."""
        request = ScraperRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            platform_hint="youtube"
        )
        assert request.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert request.platform_hint == "youtube"
    
    def test_valid_request_without_hint(self):
        """Test creating a valid request without platform hint."""
        request = ScraperRequest(url="https://example.com")
        assert request.url == "https://example.com"
        assert request.platform_hint is None
    
    def test_missing_url_raises_error(self):
        """Test that missing URL raises validation error."""
        with pytest.raises(ValueError):
            ScraperRequest()


class TestScraperResponse:
    """Test ScraperResponse Pydantic model."""
    
    def test_minimal_valid_response(self):
        """Test creating response with minimal required fields."""
        response = ScraperResponse(
            content_type=ContentType.VIDEO,
            platform="youtube",
            extraction_strategy=ExtractionStrategy.YTDLP,
            raw_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        assert response.content_type == ContentType.VIDEO
        assert response.platform == "youtube"
        assert response.extraction_strategy == ExtractionStrategy.YTDLP
        assert response.raw_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert response.title is None
        assert response.description is None
    
    def test_full_response_with_all_fields(self):
        """Test creating response with all optional fields populated."""
        response = ScraperResponse(
            title="Never Gonna Give You Up",
            description="Official music video",
            author="Rick Astley",
            content_type=ContentType.VIDEO,
            platform="youtube",
            extraction_strategy=ExtractionStrategy.YTDLP,
            thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            duration=212,
            publish_date="2009-10-25T00:00:00Z",
            raw_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        assert response.title == "Never Gonna Give You Up"
        assert response.author == "Rick Astley"
        assert response.duration == 212
        assert response.thumbnail_url is not None
    
    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raises validation error."""
        with pytest.raises(ValueError):
            ScraperResponse(
                title="Test",
                # Missing: content_type, platform, extraction_strategy, raw_url
            )
    
    def test_graceful_degradation_partial_metadata(self):
        """Test that response supports partial metadata (AC: 8)."""
        response = ScraperResponse(
            content_type=ContentType.VIDEO,
            platform="instagram",
            extraction_strategy=ExtractionStrategy.YTDLP,
            raw_url="https://instagram.com/p/test",
            title="Partial metadata test",
            # Missing: description, author, thumbnail_url, duration
        )
        assert response.title == "Partial metadata test"
        assert response.description is None
        assert response.author is None
        assert response.thumbnail_url is None


class TestCustomExceptions:
    """Test custom exception hierarchy."""
    
    def test_scraper_error_is_base_exception(self):
        """Test that ScraperError is the base exception."""
        error = ScraperError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_private_video_error_inherits_from_scraper_error(self):
        """Test PrivateVideoError inheritance."""
        error = PrivateVideoError("Video is private")
        assert isinstance(error, ScraperError)
        assert isinstance(error, Exception)
    
    def test_expired_video_error_inherits_from_scraper_error(self):
        """Test ExpiredVideoError inheritance."""
        error = ExpiredVideoError("Video has been deleted")
        assert isinstance(error, ScraperError)
    
    def test_unsupported_platform_error_inherits_from_scraper_error(self):
        """Test UnsupportedPlatformError inheritance."""
        error = UnsupportedPlatformError("Platform not supported")
        assert isinstance(error, ScraperError)
    
    def test_proxy_error_inherits_from_scraper_error(self):
        """Test ProxyError inheritance."""
        error = ProxyError("Proxy connection failed")
        assert isinstance(error, ScraperError)
    
    def test_geo_restricted_error_inherits_from_scraper_error(self):
        """Test GeoRestrictedError inheritance."""
        error = GeoRestrictedError("Content not available in your region")
        assert isinstance(error, ScraperError)
