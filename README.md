# YouTube Playlist to MP3 Converter

A Windows desktop application that downloads YouTube playlists and converts them to MP3 files with a user-friendly GUI.

## Age-Restricted Videos

Some videos are age-restricted and require authentication to download. Here are your options:

### Option 1: Export Browser Cookies (Best Method)

**For Firefox:**
1. Install the [cookies.txt extension](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Go to YouTube.com and log in
3. Click the extension icon and export cookies
4. Save as `~/.youtube_cookies.txt` (home folder)
5. Run the app

**For Chrome/Edge:**
1. Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndcbgebljdfmdjckclkclhhikea)
2. Go to YouTube.com and log in
3. Click the extension icon
4. Copy the cookies to a text file
5. Save as `~/.youtube_cookies.txt` (home folder)
6. Run the app

### Option 2: Keep Browser Logged In
Simply stay logged into YouTube in Firefox, Chrome, or Edge, and make sure the browser is **fully closed** before running the downloader.

### Option 3: Skip Age-Restricted Videos
The app will automatically skip age-restricted videos that can't be downloaded and continue with the rest.

## Features

- 🎵 Download entire YouTube playlists or single videos
- 🔊 Convert to MP3 with customizable audio quality (128-320 kbps)
- 🖥️ Easy-to-use graphical interface
- 📁 Choose custom output directory
- 📊 Real-time progress tracking and logging
- ⏸️ Stop downloads at any time
- 🚀 **Parallel downloads** - 2 concurrent videos for optimal speed
- ⚡ **Smart rate limiting** - YouTube-friendly request delays
- 🔄 **Exponential backoff** - Intelligent retry mechanism
- 💾 Remembers your last inputs

## Performance Features

### Parallel Downloads
The app downloads up to 2 videos simultaneously while respecting YouTube's rate limits. This provides:
- Faster overall playlist processing
- YouTube-friendly request rates (won't trigger detection)
- Smooth user experience with detailed progress tracking

### Rate Limiting
Built-in safeguards to avoid triggering YouTube's defense mechanisms:
- Configurable delays between video requests (default: 1.5 seconds)
- Random jitter added to requests to mimic natural browsing
- Exponential backoff on failures to avoid overwhelming the server
- Proper User-Agent headers for legitimate requests

### Fragment Downloads
Within each video:
- 3 concurrent fragment downloads per video
- Smart fragmentation with 10MB chunks
- Automatic retry on failed fragments

## Prerequisites

Before running the application, you need to install:

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **FFmpeg** (required for audio conversion)
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager
   - **Easy installation on Windows:**
     ```powershell
     # Using Chocolatey
     choco install ffmpeg
     
     # Using Scoop
     scoop install ffmpeg
     
     # Using winget
     winget install Gyan.FFmpeg
     ```
   - Alternatively, download the executable and add it to your system PATH

## Installation

1. **Clone or download this repository**
   ```bash
   cd C:\Users\zhife\youtube2mp3
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install yt-dlp ffmpeg-python
   ```

## Usage

### Method 1: Using the Batch File (Easiest)
Double-click `launch.bat` to start the application.

### Method 2: Using Python
```bash
python main.py
```

### Using the Application

1. **Enter YouTube URL**
   - Paste the YouTube playlist URL or single video URL
   - Examples:
     - Playlist: `https://www.youtube.com/playlist?list=PLxxxxxx`
     - Video: `https://www.youtube.com/watch?v=xxxxxxx`

2. **Choose Output Directory**
   - Click "Browse" to select where MP3 files will be saved
   - Default: `C:\Users\[YourName]\Music\YouTube2MP3`

3. **Select Audio Quality**
   - Choose from 128, 192, 256, or 320 kbps
   - Higher quality = larger file size
   - 192 kbps is recommended for most uses

4. **Start Download**
   - Click "Download & Convert"
   - Watch the progress in the status log
   - MP3 files will be saved to your chosen directory

5. **Stop if Needed**
   - Click "Stop" to cancel the download

## Troubleshooting

### "FFmpeg not found" error
- Make sure FFmpeg is installed and added to your system PATH
- Restart your terminal/command prompt after installing FFmpeg
- Test by running: `ffmpeg -version`

### "No module named 'yt_dlp'" error
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're using the correct Python environment

### Download fails or hangs
- Check your internet connection
- Verify the YouTube URL is correct and the video/playlist is public
- Some videos may be geo-restricted or age-restricted
- Try updating yt-dlp: `pip install --upgrade yt-dlp`

### GUI doesn't appear
- Make sure you're using Python 3.8 or higher
- tkinter should be included with Python; if not, reinstall Python

## File Structure

```
youtube2mp3/
├── main.py              # Main application with GUI
├── downloader.py        # YouTube download and conversion logic
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── launch.bat           # Windows batch file to launch app
└── README.md           # This file
```

## Audio Quality Guide

- **128 kbps**: Good for voice content, smaller file size
- **192 kbps**: Recommended - Good balance of quality and size
- **256 kbps**: Very good quality for music
- **320 kbps**: Maximum quality, larger files

## Legal Notice

This tool is for personal use only. Please respect copyright laws and YouTube's Terms of Service. Only download content you have permission to download or content that is in the public domain.

## Updates

To update the application dependencies:
```bash
pip install --upgrade yt-dlp
```

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify all prerequisites are installed correctly
3. Check the status log in the application for error messages
4. Make sure you're using the latest version of yt-dlp

## License

This project is provided as-is for educational and personal use.

## Version

Current version: 1.0.0
