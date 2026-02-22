"""
Video Downloaders for Social Media (yt-dlp) and Direct Media URLs (requests).
"""

import os
import logging
import tempfile
from typing import Optional
import yt_dlp

from .types import VideoDownloadError

logger = logging.getLogger(__name__)

import requests

class SocialVideoDownloader:
    """Downloads videos from social media platforms to a temporary file using yt-dlp."""
    
    def __init__(self, proxy_url: Optional[str] = None):
        """
        Initialize the video downloader.
        
        Args:
            proxy_url: Optional proxy URL for avoiding rate limits/geo-blocks.
        """
        self.proxy_url = proxy_url

    def download(self, url: str) -> str:
        """
        Download a video from a given URL to a temporary local file.
        
        Args:
            url: URL of the video to download.
            
        Returns:
            str: Path to the downloaded temporary video file.
            
        Raises:
            VideoDownloadError: If the download fails.
        """
        # Create a temporary file to store the video
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = temp_file.name
        temp_file.close()  # yt-dlp will write to it
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[m4a]/best[ext=mp4]/best',
            'outtmpl': temp_path,
            'quiet': True,
            'no_warnings': True,
            # User-agent spoofing to avoid bot detection
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'max_filesize': 50 * 1024 * 1024,  # AC 8 safeguarding: Max 50MB download
        }
        
        if self.proxy_url:
            ydl_opts['proxy'] = self.proxy_url
            
        cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', '/app/cookies.txt')
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        try:
            logger.info(f"Downloading video from {url} to {temp_path}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
                
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise VideoDownloadError(f"Downloaded file is empty or missing: {temp_path}")
                
            return temp_path
            
        except Exception as e:
            # Clean up the temp file if download failed
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            logger.error(f"yt-dlp failed to download {url}: {e}")
            raise VideoDownloadError(f"Failed to download video: {str(e)}")


class DirectVideoDownloader:
    """Downloads raw video files directly from a URL (e.g. Twilio MediaUrl) to a temporary file."""
    
    def download(
        self,
        video_url: str,
        auth_token: Optional[str] = None,
        account_sid: Optional[str] = None,
    ) -> str:
        """
        Download video from URL to temporary file.
        
        Args:
            video_url: URL to download video from
            auth_token: Optional authentication token (e.g., for Twilio)
            account_sid: Optional Account SID
            
        Returns:
            Path to downloaded temporary file
            
        Raises:
            VideoDownloadError: If download fails
        """
        temp_path = None
        temp_file = None
        
        try:
            # Prepare headers with authentication if provided
            headers = {}
            auth = None
            if account_sid and auth_token:
                # For Twilio MediaUrl, use HTTP Basic Auth (SID as username)
                auth = (account_sid, auth_token)
            elif auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            # Download video
            response = requests.get(video_url, headers=headers, auth=auth, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            content_type = response.headers.get('content-type', '')
            if 'mp4' in content_type or video_url.endswith('.mp4'):
                suffix = '.mp4'
            elif 'mov' in content_type or video_url.endswith('.mov'):
                suffix = '.mov'
            else:
                suffix = '.mp4'
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = temp_file.name
            
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            temp_file.close()
            return temp_path
            
        except requests.RequestException as e:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            raise VideoDownloadError(f"Failed to download video from {video_url}: {str(e)}")
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            raise VideoDownloadError(f"Unexpected error downloading video: {str(e)}")
        finally:
            if temp_file and not temp_file.closed:
                try:
                    temp_file.close()
                except Exception:
                    pass
