"""
YouTube Downloader Module
Handles downloading videos/playlists from YouTube and converting to MP3.
"""

import os
import yt_dlp
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import random


def get_ffmpeg_path():
    """Get FFmpeg path, supporting both system PATH and WinGet installation"""
    # Try to find FFmpeg in common locations
    possible_paths = [
        Path(os.getenv('LOCALAPPDATA')) / 'Microsoft' / 'WinGet' / 'Packages' / 'Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe' / 'ffmpeg-8.0.1-full_build' / 'bin' / 'ffmpeg.exe',
        Path(os.getenv('LOCALAPPDATA')) / 'Programs' / 'ffmpeg' / 'bin' / 'ffmpeg.exe',
        Path('C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe'),
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path.parent)
    
    return None


class YouTubeDownloader:
    def __init__(self, output_dir, audio_quality="192", log_callback=None, status_callback=None, progress_callback=None, skip_existing_files=True):
        """
        Initialize the YouTube downloader
        
        Args:
            output_dir: Directory to save MP3 files
            audio_quality: Audio quality in kbps (128, 192, 256, 320)
            log_callback: Callback function for logging messages
            status_callback: Callback function for status updates
            progress_callback: Callback function for progress updates (current, total)
            skip_existing_files: If True, skip files that already exist
        """
        self.output_dir = Path(output_dir)
        self.audio_quality = audio_quality
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.skip_existing_files = skip_existing_files
        self.should_stop = False
        self.current_video = 0
        self.total_videos = 0
        self.lock = threading.Lock()
        self.completed_videos = 0
        self.failed_videos = []
        self.skipped_videos = []
        self.max_workers = 2  # Conservative: 2 concurrent downloads (YouTube friendly)
        self.request_delay = 1.5  # Delay between video requests in seconds
        
    def log(self, message, level="INFO"):
        """Log a message"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
            
    def update_status(self, message):
        """Update status"""
        if self.status_callback:
            self.status_callback(message)
            
    def update_progress(self, current, total):
        """Update progress"""
        if self.progress_callback:
            self.progress_callback(current, total)
            
    def stop(self):
        """Signal to stop downloading"""
        self.should_stop = True
        
    def sanitize_filename(self, filename):
        """Sanitize filename by removing or replacing invalid characters"""
        # Characters that are invalid in Windows filenames
        invalid_chars = r'<>:"/\|?*'
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        # Remove trailing dots and spaces
        sanitized = sanitized.rstrip('. ')
        return sanitized
    
    def file_exists(self, title):
        """Check if MP3 file already exists"""
        # Sanitize the title the same way yt-dlp does
        sanitized_title = self.sanitize_filename(title)
        mp3_file = self.output_dir / f"{sanitized_title}.mp3"
        return mp3_file.exists()
        
    def progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if self.should_stop:
            raise Exception("Download stopped by user")
            
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            filename = d.get('filename', '').split(os.sep)[-1]
            
            message = f"[{self.current_video}/{self.total_videos}] {filename[:40]}... {percent} @ {speed}"
            self.update_status(message)
            
        elif d['status'] == 'finished':
            filename = d.get('filename', '').split(os.sep)[-1]
            self.log(f"Converting: {filename}")
            
        elif d['status'] == 'error':
            self.log("Download error occurred", "ERROR")
            
    def download_playlist(self, url):
        """
        Download a YouTube playlist or single video and convert to MP3
        
        Args:
            url: YouTube URL (playlist or single video)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if URL is valid
            if not url.startswith(('http://', 'https://')):
                self.log("Invalid URL format", "ERROR")
                return False
                
            self.log(f"Processing URL: {url}")
            
            # Try different browsers for cookies (Firefox works best while browser is open)
            browsers = ['firefox', 'edge', 'chrome', 'safari', 'opera']
            cookie_browser = None
            
            for browser in browsers:
                try:
                    # Test if browser cookies are accessible
                    import tempfile
                    test_opts = {
                        'cookiesfrombrowser': (browser,), 
                        'quiet': True,
                        'paths': {'temp': tempfile.gettempdir()}
                    }
                    with yt_dlp.YoutubeDL(test_opts) as test_ydl:
                        # Try to access the cookiejar to test
                        _ = test_ydl.cookiejar
                        cookie_browser = browser
                        self.log(f"Using cookies from {browser.title()} browser")
                        break
                except Exception as e:
                    continue
            
            if not cookie_browser:
                self.log("Could not access browser cookies. For age-restricted videos: Close Chrome/Edge or use Firefox.", "WARNING")
            
            # Extract playlist info first
            self.log("Extracting video/playlist information...")
            extract_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
            }
            
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    # It's a playlist
                    videos = [entry for entry in info['entries'] if entry is not None]
                    self.total_videos = len(videos)
                    self.log(f"Found playlist with {self.total_videos} videos")
                    self.update_status(f"Processing playlist ({self.total_videos} videos)")
                    self.update_progress(0, self.total_videos)
                    
                    # First pass: identify and skip existing files with progress updates
                    videos_to_download = []
                    for i, video in enumerate(videos, 1):
                        title = video.get('title', 'Unknown')
                        if self.skip_existing_files and self.file_exists(title):
                            self.log(f"⊘ Skipped (already exists): {title}")
                            self.skipped_videos.append(title)
                            with self.lock:
                                self.completed_videos += 1
                            # Update progress immediately for skipped files
                            self.update_progress(self.completed_videos, self.total_videos)
                            time.sleep(0.15)  # Wait longer to match GUI update delay (100ms) plus buffer
                        else:
                            videos_to_download.append((i, video))
                    
                    # Download videos with parallel processing
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = {}
                        for i, video in videos_to_download:
                            if self.should_stop:
                                break
                            
                            # Submit download task
                            future = executor.submit(
                                self._download_single_video_safe,
                                i,
                                self.total_videos,
                                video
                            )
                            futures[future] = (i, video.get('title', 'Unknown'))
                            
                            # Respect rate limits - add delay between submissions
                            time.sleep(self.request_delay + random.uniform(0, 0.5))
                        
                        # Process completed downloads
                        for future in as_completed(futures):
                            if self.should_stop:
                                executor.shutdown(wait=False, cancel_futures=True)
                                break
                            
                            video_num, title = futures[future]
                            try:
                                result = future.result()
                                with self.lock:
                                    self.completed_videos += 1
                                # Update progress for both successful and failed downloads
                                self.update_progress(self.completed_videos, self.total_videos)
                                # Longer delay to let GUI render each update sequentially
                                time.sleep(0.15)
                                if not result:
                                    self.failed_videos.append(title)
                            except Exception as e:
                                self.log(f"Error processing video {video_num}: {str(e)}", "ERROR")
                                self.failed_videos.append(title)
                else:
                    # Single video
                    self.total_videos = 1
                    self.current_video = 1
                    self.log("Found single video")
                    self.update_status("Processing video")
                    self.update_progress(0, 1)
                    
                    # Download using the safe method
                    success = self._download_single_video_safe(1, 1, {'id': url.split('v=')[-1].split('&')[0], 'title': 'Video'})
                    if success:
                        self.update_progress(1, 1)
            
            if not self.should_stop:
                self.log("All downloads completed!", "SUCCESS")
                if self.skipped_videos:
                    self.log(f"Skipped {len(self.skipped_videos)} existing files", "INFO")
                if self.failed_videos:
                    self.log(f"Failed to download {len(self.failed_videos)} age-restricted videos (requires authentication)", "WARNING")
                self.update_status("Completed")
                return True
            else:
                return False
                
        except Exception as e:
            if "stopped by user" in str(e).lower():
                self.log("Download cancelled by user", "WARNING")
            else:
                self.log(f"Error during download: {str(e)}", "ERROR")
            return False
            
    def _download_single_video_safe(self, video_num, total_videos, video):
        """
        Safely download a single video with error handling
        Used by ThreadPoolExecutor for parallel downloads
        """
        try:
            if self.should_stop:
                return False
                
            title = video.get('title', 'Unknown')
            video_id = video.get('id', '')
            video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else video.get('url', '')
            
            with self.lock:
                self.current_video = video_num
            

            self.log(f"[{video_num}/{total_videos}] Downloading: {title}")
            self.update_status(f"[{video_num}/{total_videos}] {title[:50]}...")
            
            if not video_url:
                self.log(f"Skipping video {video_num}: No valid URL", "WARNING")
                return False
            
            # Configure yt-dlp options for this download
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': self.audio_quality,
                }],
                'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
                'quiet': True,  # Reduce noise for parallel downloads
                'no_warnings': True,
                'ignoreerrors': True,
                'skip_unavailable_fragments': True,
                'nocheckcertificate': True,
                'prefer_ffmpeg': True,
                'ffmpeg_location': get_ffmpeg_path() or None,
                'keepvideo': False,
                'writethumbnail': False,
                'concurrent_fragment_downloads': 3,  # Moderate parallelization
                'http_chunk_size': 10485760,
                'retries': 5,
                'fragment_retries': 5,
                'socket_timeout': 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            # Add exponential backoff for retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                    self.log(f"✓ Completed: {title}", "SUCCESS")
                    return True
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt + random.uniform(0, 1)  # Exponential backoff
                        self.log(f"Retry {attempt + 1}/{max_retries - 1} for {title} after {wait_time:.1f}s", "WARNING")
                        time.sleep(wait_time)
                    else:
                        error_msg = str(e)
                        if "age" in error_msg.lower() or "sign in" in error_msg.lower():
                            self.log(f"⚠ Skipped (age-restricted): {title}", "WARNING")
                        else:
                            self.log(f"✗ Failed: {title} - {str(e)[:100]}", "ERROR")
                        return False
                        
        except Exception as e:
            self.log(f"Error downloading video {video_num}: {str(e)}", "ERROR")
            return False
    
    def download_single_video(self, url):
        """
        Download a single YouTube video and convert to MP3
        
        Args:
            url: YouTube video URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.download_playlist(url)  # Same method works for both
        
    def get_video_info(self, url):
        """
        Get information about a YouTube video or playlist without downloading
        
        Args:
            url: YouTube URL
            
        Returns:
            dict: Video/playlist information or None if error
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
                
        except Exception as e:
            self.log(f"Error getting video info: {str(e)}", "ERROR")
            return None
