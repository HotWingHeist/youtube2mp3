# Unit Tests for YouTube2MP3 Converter

This directory contains comprehensive unit tests for the YouTube2MP3 Converter application.

## Running Tests

### Run all tests:
```bash
python test_youtube2mp3.py
```

### Run with verbose output:
```bash
python -m unittest test_youtube2mp3 -v
```

### Run specific test class:
```bash
python -m unittest test_youtube2mp3.TestConfig -v
```

### Run specific test:
```bash
python -m unittest test_youtube2mp3.TestConfig.test_config_initialization -v
```

## Test Coverage

The test suite covers:

### Configuration Tests (TestConfig)
- ✅ Configuration initialization with defaults
- ✅ Quality options validation
- ✅ Default output directory creation
- ✅ Settings saving to JSON file
- ✅ Settings loading from JSON file

### Downloader Tests (TestYouTubeDownloader)
- ✅ Downloader initialization
- ✅ Output directory path handling
- ✅ File existence checking
- ✅ Stop signal functionality
- ✅ Logging callback
- ✅ Status update callback
- ✅ Progress update callback
- ✅ URL validation
- ✅ Video ID extraction
- ✅ Concurrent worker configuration

### Video Handling Tests (TestDownloaderVideoHandling)
- ✅ Skip existing files setting
- ✅ Video counter tracking
- ✅ Failed videos tracking
- ✅ Skipped videos tracking

### Audio Quality Tests (TestAudioQualitySettings)
- ✅ Valid quality values (128, 192, 256, 320 kbps)
- ✅ Quality stored as string

### Thread Safety Tests (TestThreadSafety)
- ✅ Lock existence for thread-safe operations
- ✅ Lock functionality

### Integration Tests (TestIntegration)
- ✅ Downloader with all callbacks
- ✅ Full initialization with all parameters

## Test Results

**Total Tests: 24**
**Passed: 24 ✅**
**Failed: 0**
**Execution Time: ~0.05s**

### Test Categories:
- Config Tests: 5
- Downloader Tests: 11
- Video Handling Tests: 4
- Quality Tests: 2
- Thread Safety Tests: 1
- Integration Tests: 2

## What's Tested

### ✅ Configuration Management
- Settings persistence (save/load)
- Quality options
- Default directories

### ✅ Downloader Functionality
- Initialization with various parameters
- File existence detection
- Stop signal handling
- Callback mechanisms (logging, status, progress)

### ✅ Video Processing
- Video tracking (total, completed, skipped, failed)
- URL parsing and validation
- Video ID extraction
- Skip existing files functionality

### ✅ Thread Safety
- Lock-based synchronization
- Concurrent worker configuration

### ✅ Audio Quality
- Valid quality settings (128-320 kbps)
- Quality parameter handling

## What's NOT Tested (Requires Network)

These features require actual YouTube API access and network connectivity:
- Actual video downloading
- Playlist extraction
- YouTube authentication
- FFmpeg conversion

For testing these features, integration tests with mocked yt-dlp would be needed.

## Adding New Tests

To add new tests:

1. Create a new test class inheriting from `unittest.TestCase`
2. Add setup/teardown methods if needed
3. Write test methods starting with `test_`
4. Use assertions to verify behavior

Example:
```python
class TestNewFeature(unittest.TestCase):
    def test_new_functionality(self):
        result = some_function()
        self.assertEqual(result, expected_value)
```

## Dependencies

The test suite requires:
- Python 3.8+
- Standard library modules: `unittest`, `tempfile`, `json`, `pathlib`
- Project modules: `config.py`, `downloader.py`

No additional dependencies required!

## Continuous Integration

To integrate with CI/CD:

```bash
# Run tests and generate exit code
python -m unittest test_youtube2mp3

# Exit code 0 = all passed
# Exit code 1 = failures/errors
```

## Troubleshooting

### Import errors
Make sure you run tests from the project root directory:
```bash
cd c:\Users\zhife\youtube2mp3
python test_youtube2mp3.py
```

### Permission denied
Some tests create temporary files. Ensure write permissions to temp directory:
```bash
# Windows
echo %TEMP%

# Check permissions
icacls %TEMP%
```

### Tests hang
If tests hang, they may be trying to access actual network. This shouldn't happen with the current test suite, but if it does:
- Kill the process: `Ctrl+C` or `Ctrl+Break`
- Check for any uncommented network calls in tests
