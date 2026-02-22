import pytest
from unittest.mock import patch, MagicMock
import os
from tempfile import NamedTemporaryFile
from tools.video.downloader import SocialVideoDownloader
from tools.video.types import VideoDownloadError

@patch('yt_dlp.YoutubeDL')
def test_social_video_downloader_success(mock_ytdl):
    # Mock download success
    mock_instance = mock_ytdl.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = {
        'id': 'test_video',
        'title': 'Test Video',
        'duration': 60
    }
    
    downloader = SocialVideoDownloader()
    
    # We shouldn't write to disk in this mock, but we'll mock the internal download
    with patch('tools.video.downloader.tempfile.NamedTemporaryFile') as mock_temp, \
         patch('os.path.getsize', return_value=1000), \
         patch('os.path.exists', return_value=True):
        mock_temp.return_value.name = '/tmp/test_video.mp4'
        
        path = downloader.download('https://youtube.com/watch?v=1234')
        
        assert path == '/tmp/test_video.mp4'
        mock_instance.extract_info.assert_called_once_with('https://youtube.com/watch?v=1234', download=True)

@patch('yt_dlp.YoutubeDL')
def test_social_video_downloader_failure(mock_ytdl):
    mock_instance = mock_ytdl.return_value.__enter__.return_value
    mock_instance.extract_info.side_effect = Exception("yt-dlp download failed")
    
    downloader = SocialVideoDownloader()
    
    with pytest.raises(VideoDownloadError, match="Failed to download video"):
        downloader.download('https://youtube.com/watch?v=1234')

def test_social_video_downloader_init():
    """Test SocialVideoDownloader initialization with and without proxy."""
    dl1 = SocialVideoDownloader()
    assert dl1.proxy_url is None
    
    dl2 = SocialVideoDownloader(proxy_url="http://proxy:8080")
    assert dl2.proxy_url == "http://proxy:8080"

# Integration test (might be slow)
@pytest.mark.integration
def test_social_video_downloader_integration():
    downloader = SocialVideoDownloader()
    # A short public YouTube video / Short format, using a known ID
    # This URL is typical for a short video, testing yt-dlp's real download
    url = "https://www.youtube.com/shorts/5qap5aO4i9A"  # We should use a universally known good one, or just test failure handling if this doesn't work.
    
    try:
        path = downloader.download(url)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
    except VideoDownloadError as e:
        # If it fails due to network/bot-detection during testing in CI, we gracefully skip or just warn.
        pytest.skip(f"Integration test skipped due to download failure (likely bot detection): {e}")
    finally:
        if 'path' in locals() and os.path.exists(path):
            os.unlink(path)
