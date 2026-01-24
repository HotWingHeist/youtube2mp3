"""
YouTube Playlist to MP3 Converter
A Windows application to download YouTube playlists and convert them to MP3 files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
from downloader import YouTubeDownloader
from config import Config


class YouTube2MP3App:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Playlist to MP3 Converter")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.config = Config()
        self.downloader = None
        self.is_downloading = False
        self.progress_event = threading.Event()  # Synchronize progress updates
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # YouTube URL input
        ttk.Label(main_frame, text="YouTube Playlist URL:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.url_entry = ttk.Entry(main_frame, width=50)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        # Load last URL
        if self.config.last_url:
            self.url_entry.insert(0, self.config.last_url)
        
        # Info label for age-restricted videos
        info_label = ttk.Label(
            main_frame, 
            text="💡 Age-restricted videos: Stay logged into YouTube in Firefox, Chrome, or Edge",
            font=('TkDefaultFont', 8),
            foreground='blue'
        )
        info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Output directory selection
        ttk.Label(main_frame, text="Output Directory:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        # Load last output directory
        self.dir_entry.insert(0, self.config.last_output_dir)
        
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(
            row=0, column=1
        )
        
        # Quality selection
        ttk.Label(main_frame, text="Audio Quality:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Load last quality setting
        self.quality_var = tk.StringVar(value=self.config.last_quality)
        qualities = [("128 kbps", "128"), ("192 kbps", "192"), ("256 kbps", "256"), ("320 kbps", "320")]
        
        for i, (text, value) in enumerate(qualities):
            ttk.Radiobutton(
                quality_frame, text=text, variable=self.quality_var, value=value
            ).grid(row=0, column=i, padx=5)
        
        # Skip existing files option
        ttk.Label(main_frame, text="Options:").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        
        self.skip_existing_var = tk.BooleanVar(value=self.config.last_skip_existing)
        ttk.Checkbutton(
            main_frame, text="Skip existing files (don't re-download)", variable=self.skip_existing_var
        ).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.download_btn = ttk.Button(
            button_frame, text="Download & Convert", command=self.start_download
        )
        self.download_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame, text="Stop", command=self.stop_download, state=tk.DISABLED
        )
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame, text="Clear Log", command=self.clear_log
        ).grid(row=0, column=2, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame, mode='determinate', maximum=100, length=300
        )
        self.progress.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Log output
        log_label = ttk.Label(main_frame, text="Status Log:")
        log_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame, height=15, width=70, state=tk.DISABLED
        )
        self.log_text.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
    def browse_directory(self):
        """Open directory browser dialog"""
        directory = filedialog.askdirectory(
            initialdir=self.dir_entry.get(),
            title="Select Output Directory"
        )
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            
    def log(self, message, level="INFO"):
        """Add message to log (thread-safe)"""
        def _log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{level}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(0, _log)
        
    def clear_log(self):
        """Clear the log text"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def update_status(self, message):
        """Update status bar (thread-safe)"""
        self.root.after(0, lambda: self.status_var.set(message))
        
    def update_progress(self, current, total):
        """Update progress bar (thread-safe with synchronization)"""
        def _update():
            if total > 0:
                percentage = (current / total) * 100
                self.progress['value'] = percentage
                self.root.update()
            self.progress_event.set()  # Signal that update is complete
        
        self.progress_event.clear()  # Reset event
        # Immediate update - downloader throttles with time.sleep(0.15)
        self.root.after(0, _update)
        
    def start_download(self):
        """Start the download process"""
        url = self.url_entry.get().strip()
        output_dir = self.dir_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube URL")
            return
            
        if not output_dir:
            messagebox.showwarning("Warning", "Please select an output directory")
            return
        
        # Save settings for next time
        self.config.save_settings(
            url=url,
            output_dir=output_dir,
            quality=self.quality_var.get(),
            skip_existing=self.skip_existing_var.get()
        )
            
        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create output directory: {str(e)}")
            return
            
        # Disable controls
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.url_entry.config(state=tk.DISABLED)
        self.dir_entry.config(state=tk.DISABLED)
        
        # Reset progress bar
        self.progress['value'] = 0
        
        self.is_downloading = True
        self.log("Starting download process...")
        self.update_status("Downloading...")
        
        # Start download in separate thread
        quality = self.quality_var.get()
        skip_existing = self.skip_existing_var.get()
        thread = threading.Thread(
            target=self.download_thread,
            args=(url, output_dir, quality, skip_existing),
            daemon=True
        )
        thread.start()
        
    def download_thread(self, url, output_dir, quality, skip_existing=True):
        """Thread function for downloading"""
        try:
            self.downloader = YouTubeDownloader(
                output_dir=output_dir,
                audio_quality=quality,
                log_callback=self.log,
                status_callback=self.update_status,
                progress_callback=self.update_progress,
                skip_existing_files=skip_existing
            )
            
            success = self.downloader.download_playlist(url)
            
            if success and self.is_downloading:
                self.log("Download completed successfully!", "SUCCESS")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Playlist downloaded and converted to MP3!\nLocation: {output_dir}"
                ))
            elif not self.is_downloading:
                self.log("Download stopped by user", "WARNING")
            else:
                self.log("Download completed with errors", "WARNING")
                
        except Exception as e:
            self.log(f"Error: {str(e)}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                f"An error occurred:\n{str(e)}"
            ))
        finally:
            self.root.after(0, self.download_finished)
            
    def stop_download(self):
        """Stop the download process"""
        self.is_downloading = False
        if self.downloader:
            self.downloader.stop()
        self.log("Stopping download...", "WARNING")
        self.update_status("Stopping...")
        
    def download_finished(self):
        """Clean up after download finishes"""
        self.progress['value'] = 100
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.url_entry.config(state=tk.NORMAL)
        self.dir_entry.config(state=tk.NORMAL)
        self.update_status("Ready")
        self.is_downloading = False


def main():
    """Main entry point"""
    root = tk.Tk()
    app = YouTube2MP3App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
