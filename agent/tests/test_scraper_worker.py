import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from unittest.mock import patch, MagicMock
from tools.scraper.types import ScraperResponse, ContentType, ExtractionStrategy

# We mock env vars before importing ScraperWorker
with patch.dict('os.environ', {'SUPABASE_URL': 'http://mock', 'SUPABASE_SERVICE_ROLE_KEY': 'mock'}):
    from scraper_worker import ScraperWorker

@pytest.fixture
def mock_worker():
    with patch('scraper_worker.create_client'), \
         patch('scraper_worker.get_messaging_provider'), \
         patch('scraper_worker.ScraperService'), \
         patch('scraper_worker.NormalizerService'), \
         patch('scraper_worker.SummarizerService'):
        worker = ScraperWorker()
        worker.supabase = MagicMock()
        worker.messaging = MagicMock()
        worker.scraper_service = MagicMock()
        worker.normalizer_service = MagicMock()
        worker.summarizer_service = MagicMock()
        yield worker

@patch('scraper_worker.hashlib.sha256')
@patch('tools.video.service.VideoProcessingService')
@patch('tools.video.downloader.SocialVideoDownloader')
def test_process_and_update_video_success(mock_downloader_cls, mock_video_svc_cls, mock_hash, mock_worker):
    """Test successful video processing integration."""
    # Setup mocks
    mock_hash.return_value.hexdigest.return_value = 'test_hash'
    mock_worker.supabase.table().select().eq().limit().execute.return_value.data = []  # No existing link
    
    mock_worker.scraper_service.scrape.return_value = MagicMock(
        title="Test Video",
        description="desc",
        content_type=ContentType.VIDEO,
        platform="youtube",
        extraction_strategy=ExtractionStrategy.YTDLP,
        raw_url="http://test.com/vid"
    )
    
    mock_worker.normalizer_service.normalize.return_value = MagicMock(
        category=Category.ENTERTAINMENT,
        tags=["fun"],
        price_range=PriceRange.UNKNOWN
    )
    
    mock_worker.summarizer_service.generate_summary.return_value = "Text summary"
    
    # Video mocks
    mock_dl = mock_downloader_cls.return_value
    mock_dl.download.return_value = '/tmp/fake_video.mp4'
    
    mock_vs = mock_video_svc_cls.return_value
    mock_vs.process_video.return_value.summary = "Visual summary"
    
    # Mock OS unlinking
    with patch('os.path.exists', return_value=True), patch('os.unlink') as mock_unlink:
        
        job = {'id': 'job1', 'payload': {'Body': 'http://test.com/vid', 'From': '123'}}
        
        mock_worker.process_and_update(job)
        
        mock_dl.download.assert_called_once_with('http://test.com/vid')
        mock_vs.process_video.assert_called_once()
        mock_unlink.assert_called_once_with('/tmp/fake_video.mp4')


@patch('scraper_worker.hashlib.sha256')
@patch('tools.video.downloader.SocialVideoDownloader')
def test_process_and_update_video_fallback(mock_downloader_cls, mock_hash, mock_worker):
    """Test that video download failure gracefully falls back to text-only with warning."""
    mock_hash.return_value.hexdigest.return_value = 'test_hash'
    mock_worker.supabase.table().select().eq().limit().execute.return_value.data = []
    
    # Needs to be an object with dot notation access because scraper_worker does `metadata.content_type`
    class MockMetadata:
        title = "Test Video"
        description = "desc"
        author = "author"
        thumbnail_url = "thumb"
        content_type = ContentType.VIDEO
        platform = "instagram"
        extraction_strategy = ExtractionStrategy.YTDLP
        raw_url = "http://test.com/vid"
        visual_summary = None

    mock_worker.scraper_service.scrape.return_value = MockMetadata()
    mock_worker.normalizer_service.normalize.return_value = MagicMock(
        category=MagicMock(value="entertainment"), 
        price_range=MagicMock(value="unknown"), 
        tags=[]
    )
    mock_worker.summarizer_service.generate_summary.return_value = "Text summary"
    
    mock_dl = mock_downloader_cls.return_value
    mock_dl.download.side_effect = Exception("yt-dlp blocked")
    
    job = {'id': 'job2', 'payload': {'Body': 'http://test.com/vid', 'From': '123'}}
    
    result = mock_worker.process_and_update(job)
    
    assert result is True  # Should succeed, just with warning added
    
    # Verify the fallback warning was added to AI summary
    mock_worker.supabase.table().insert.assert_called()
    insert_call = mock_worker.supabase.table().insert.call_args[0][0]
    
    assert "Text summary" in insert_call['ai_summary']
    assert "⚠️ Visual extraction failed or was blocked by the platform." in insert_call['ai_summary']
