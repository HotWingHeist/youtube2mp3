"""
Configuration settings for YouTube2MP3 Converter
"""

import os
import json
from pathlib import Path


class Config:
    """Application configuration"""
    
    def __init__(self):
        # Settings file location
        self.settings_file = Path.home() / ".youtube2mp3_settings.json"
        
        # Default output directory (user's Music folder)
        self.default_output_dir = Path.home() / "Music" / "YouTube2MP3"
        
        # Create default directory if it doesn't exist
        try:
            self.default_output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to Desktop if Music folder doesn't exist
            self.default_output_dir = Path.home() / "Desktop" / "YouTube2MP3"
            self.default_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load saved settings
        self.last_url = ""
        self.last_output_dir = str(self.default_output_dir)
        self.last_quality = "192"
        self.last_skip_existing = True  # Default: skip existing files
        self.load_settings()
        
        # Audio quality options (in kbps)
        self.quality_options = {
            '128': '128 kbps',
            '192': '192 kbps',
            '256': '256 kbps',
            '320': '320 kbps'
        }
        
        # Default audio quality
        self.default_quality = '192'
        
        # Application metadata
        self.app_name = "YouTube Playlist to MP3 Converter"
        self.version = "1.0.0"
        self.author = "Your Name"
        
        # FFmpeg settings
        self.ffmpeg_location = None  # None = use system FFmpeg or yt-dlp bundled version
        
        # Cookies settings
        self.cookies_file = Path.home() / '.youtube_cookies.txt'  # Path to cookies file if user has one
        
        # Download settings
        self.max_retries = 3
        self.timeout = 300  # seconds
        
        # UI settings
        self.window_width = 800
        self.window_height = 600
        
    def get_output_template(self):
        """Get the output filename template"""
        return "%(title)s.%(ext)s"
        
    def get_ffmpeg_location(self):
        """Get FFmpeg location if set"""
        return self.ffmpeg_location
    
    def save_settings(self, url="", output_dir="", quality="192", skip_existing=True):
        """Save user settings to file"""
        settings = {
            'last_url': url,
            'last_output_dir': output_dir,
            'last_quality': quality,
            'last_skip_existing': skip_existing
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Could not save settings: {e}")
    
    def load_settings(self):
        """Load user settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.last_url = settings.get('last_url', '')
                    self.last_output_dir = settings.get('last_output_dir', str(self.default_output_dir))
                    self.last_quality = settings.get('last_quality', '192')
                    self.last_skip_existing = settings.get('last_skip_existing', True)
        except Exception as e:
            print(f"Could not load settings: {e}")
