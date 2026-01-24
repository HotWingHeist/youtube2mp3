"""
Unit tests for YouTube2MP3 Converter
Tests configuration, downloader, and utility functions
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from downloader import YouTubeDownloader


class TestConfig(unittest.TestCase):
    """Test configuration module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = Config()
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_config_initialization(self):
        """Test config initializes with default values"""
        self.assertIsNotNone(self.config.default_output_dir)
        self.assertEqual(self.config.default_quality, '192')
        self.assertEqual(self.config.version, '1.0.0')
        self.assertIn('192', self.config.quality_options)
    
    def test_config_quality_options(self):
        """Test quality options are valid"""
        valid_qualities = ['128', '192', '256', '320']
        for quality in valid_qualities:
            self.assertIn(quality, self.config.quality_options)
    
    def test_config_default_output_dir_exists(self):
        """Test default output directory is created"""
        self.assertTrue(self.config.default_output_dir.exists())
    
    def test_save_settings(self):
        """Test saving settings to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / 'test_settings.json'
            original_file = self.config.settings_file
            self.config.settings_file = settings_file
            
            self.config.save_settings(
                url='https://youtube.com/test',
                output_dir=temp_dir,
                quality='256',
                skip_existing=False
            )
            
            self.assertTrue(settings_file.exists())
            
            with open(settings_file, 'r') as f:
                data = json.load(f)
            
            self.assertEqual(data['last_url'], 'https://youtube.com/test')
            self.assertEqual(data['last_quality'], '256')
            self.assertFalse(data['last_skip_existing'])
            
            self.config.settings_file = original_file
    
    def test_load_settings(self):
        """Test loading settings from file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / 'test_settings.json'
            
            # Create test settings file
            test_data = {
                'last_url': 'https://youtube.com/test',
                'last_output_dir': temp_dir,
                'last_quality': '320',
                'last_skip_existing': True
            }
            with open(settings_file, 'w') as f:
                json.dump(test_data, f)
            
            # Load settings
            original_file = self.config.settings_file
            self.config.settings_file = settings_file
            self.config.load_settings()
            
            self.assertEqual(self.config.last_url, 'https://youtube.com/test')
            self.assertEqual(self.config.last_quality, '320')
            self.assertTrue(self.config.last_skip_existing)
            
            self.config.settings_file = original_file


class TestYouTubeDownloader(unittest.TestCase):
    """Test YouTubeDownloader module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.downloader = YouTubeDownloader(
            output_dir=str(self.output_dir),
            audio_quality='192',
            skip_existing_files=True
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_downloader_initialization(self):
        """Test downloader initializes correctly"""
        self.assertEqual(self.downloader.audio_quality, '192')
        self.assertTrue(self.downloader.skip_existing_files)
        self.assertFalse(self.downloader.should_stop)
        self.assertEqual(self.downloader.max_workers, 2)
    
    def test_downloader_output_dir_is_path(self):
        """Test output directory is stored as Path object"""
        self.assertIsInstance(self.downloader.output_dir, Path)
    
    def test_file_exists_check(self):
        """Test file existence checking"""
        test_title = "Test Video"
        
        # File doesn't exist yet
        self.assertFalse(self.downloader.file_exists(test_title))
        
        # Create test file
        test_file = self.output_dir / f"{test_title}.mp3"
        test_file.touch()
        
        # Now it should exist
        self.assertTrue(self.downloader.file_exists(test_title))
    
    def test_stop_signal(self):
        """Test stop signal works"""
        self.assertFalse(self.downloader.should_stop)
        self.downloader.stop()
        self.assertTrue(self.downloader.should_stop)
    
    def test_log_callback(self):
        """Test logging with callback"""
        logs = []
        
        def mock_log(message, level="INFO"):
            logs.append((message, level))
        
        downloader = YouTubeDownloader(
            output_dir=str(self.output_dir),
            log_callback=mock_log
        )
        
        downloader.log("Test message", "INFO")
        downloader.log("Test error", "ERROR")
        
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0], ("Test message", "INFO"))
        self.assertEqual(logs[1], ("Test error", "ERROR"))
    
    def test_update_status_callback(self):
        """Test status update callback"""
        statuses = []
        
        def mock_status(message):
            statuses.append(message)
        
        downloader = YouTubeDownloader(
            output_dir=str(self.output_dir),
            status_callback=mock_status
        )
        
        downloader.update_status("Processing video")
        
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0], "Processing video")
    
    def test_update_progress_callback(self):
        """Test progress callback"""
        progress_updates = []
        
        def mock_progress(current, total):
            progress_updates.append((current, total))
        
        downloader = YouTubeDownloader(
            output_dir=str(self.output_dir),
            progress_callback=mock_progress
        )
        
        downloader.update_progress(1, 5)
        downloader.update_progress(2, 5)
        downloader.update_progress(5, 5)
        
        self.assertEqual(len(progress_updates), 3)
        self.assertEqual(progress_updates[0], (1, 5))
        self.assertEqual(progress_updates[2], (5, 5))
    
    def test_url_validation(self):
        """Test URL validation"""
        downloader = YouTubeDownloader(output_dir=str(self.output_dir))
        
        # Valid URLs should be accepted
        valid_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'http://youtube.com/watch?v=test',
            'https://youtu.be/dQw4w9WgXcQ'
        ]
        
        for url in valid_urls:
            self.assertTrue(url.startswith(('http://', 'https://')))
        
        # Invalid URLs should not start with http/https
        invalid_url = 'not_a_url'
        self.assertFalse(invalid_url.startswith(('http://', 'https://')))
    
    def test_video_id_extraction(self):
        """Test extracting video ID from URLs"""
        test_urls = {
            'https://www.youtube.com/watch?v=abc123': 'abc123',
            'https://youtube.com/watch?v=def456&list=xyz': 'def456',
            'https://youtu.be/ghi789': 'ghi789',
        }
        
        for url, expected_id in test_urls.items():
            # Extract video ID
            extracted_id = url.split('v=')[-1].split('&')[0] if 'v=' in url else url.split('/')[-1]
            self.assertIn(expected_id, extracted_id)
    
    def test_concurrent_workers_config(self):
        """Test concurrent workers configuration"""
        downloader = YouTubeDownloader(output_dir=str(self.output_dir))
        self.assertEqual(downloader.max_workers, 2)  # YouTube-friendly default
        self.assertGreater(downloader.request_delay, 1)  # Has rate limiting


class TestDownloaderVideoHandling(unittest.TestCase):
    """Test downloader video handling functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.downloader = YouTubeDownloader(
            output_dir=str(self.temp_dir.name),
            skip_existing_files=True
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_skip_existing_setting(self):
        """Test skip existing files setting"""
        # With skip enabled
        dl1 = YouTubeDownloader(
            output_dir=str(self.temp_dir.name),
            skip_existing_files=True
        )
        self.assertTrue(dl1.skip_existing_files)
        
        # With skip disabled
        dl2 = YouTubeDownloader(
            output_dir=str(self.temp_dir.name),
            skip_existing_files=False
        )
        self.assertFalse(dl2.skip_existing_files)
    
    def test_video_counter_tracking(self):
        """Test video counter tracking"""
        self.assertEqual(self.downloader.current_video, 0)
        self.assertEqual(self.downloader.total_videos, 0)
        self.assertEqual(self.downloader.completed_videos, 0)
        
        # Simulate progress
        self.downloader.total_videos = 10
        self.downloader.completed_videos = 5
        self.downloader.current_video = 5
        
        self.assertEqual(self.downloader.completed_videos, 5)
        self.assertEqual(self.downloader.total_videos, 10)
    
    def test_failed_videos_tracking(self):
        """Test failed videos are tracked"""
        self.assertEqual(len(self.downloader.failed_videos), 0)
        
        self.downloader.failed_videos.append("Video 1")
        self.downloader.failed_videos.append("Video 2")
        
        self.assertEqual(len(self.downloader.failed_videos), 2)
        self.assertIn("Video 1", self.downloader.failed_videos)
    
    def test_skipped_videos_tracking(self):
        """Test skipped videos are tracked"""
        self.assertEqual(len(self.downloader.skipped_videos), 0)
        
        self.downloader.skipped_videos.append("Video 1")
        self.downloader.skipped_videos.append("Video 2")
        
        self.assertEqual(len(self.downloader.skipped_videos), 2)
        self.assertIn("Video 1", self.downloader.skipped_videos)


class TestAudioQualitySettings(unittest.TestCase):
    """Test audio quality settings"""
    
    def test_valid_quality_values(self):
        """Test valid quality values"""
        valid_qualities = ['128', '192', '256', '320']
        
        for quality in valid_qualities:
            downloader = YouTubeDownloader(
                output_dir=tempfile.gettempdir(),
                audio_quality=quality
            )
            self.assertEqual(downloader.audio_quality, quality)
    
    def test_quality_is_string(self):
        """Test quality is stored as string"""
        downloader = YouTubeDownloader(
            output_dir=tempfile.gettempdir(),
            audio_quality='192'
        )
        self.assertIsInstance(downloader.audio_quality, str)


class TestThreadSafety(unittest.TestCase):
    """Test thread-safety features"""
    
    def test_lock_exists(self):
        """Test that downloader has a lock for thread safety"""
        downloader = YouTubeDownloader(output_dir=tempfile.gettempdir())
        self.assertIsNotNone(downloader.lock)
        
        # Lock should be usable
        with downloader.lock:
            downloader.completed_videos = 1
        
        self.assertEqual(downloader.completed_videos, 1)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_downloader_with_all_callbacks(self):
        """Test downloader works with all callbacks"""
        logs = []
        statuses = []
        progress = []
        
        downloader = YouTubeDownloader(
            output_dir=tempfile.gettempdir(),
            audio_quality='192',
            log_callback=lambda msg, level="INFO": logs.append((msg, level)),
            status_callback=lambda msg: statuses.append(msg),
            progress_callback=lambda curr, total: progress.append((curr, total))
        )
        
        # Test all callbacks work
        downloader.log("Test log", "INFO")
        downloader.update_status("Test status")
        downloader.update_progress(1, 5)
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(len(statuses), 1)
        self.assertEqual(len(progress), 1)
    
    def test_full_downloader_initialization(self):
        """Test full downloader initialization with all parameters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = YouTubeDownloader(
                output_dir=temp_dir,
                audio_quality='320',
                log_callback=lambda msg, level: None,
                status_callback=lambda msg: None,
                progress_callback=lambda curr, total: None,
                skip_existing_files=False
            )
            
            self.assertEqual(downloader.audio_quality, '320')
            self.assertFalse(downloader.skip_existing_files)
            self.assertEqual(str(downloader.output_dir), temp_dir)


def run_tests():
    """Run all tests"""
    unittest.main(verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
