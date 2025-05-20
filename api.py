import os
import json
import yt_dlp
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import tempfile
from pathlib import Path


class DownloadFormat(Enum):
    """Supported download formats"""
    MP4_BEST = "best[ext=mp4]"
    MP4_720P = "best[height<=720][ext=mp4]"
    MP4_480P = "best[height<=480][ext=mp4]"
    MP3_BEST = "bestaudio[ext=m4a]/bestaudio/best"
    AUDIO_ONLY = "bestaudio/best"


@dataclass
class VideoInfo:
    """Data class to store video information"""
    id: str
    title: str
    description: str
    duration: int
    uploader: str
    upload_date: str
    view_count: int
    thumbnail: str
    formats: List[Dict[str, Any]]
    url: str


@dataclass
class DownloadProgress:
    """Data class to store download progress information"""
    status: str  # downloading, finished, error
    percentage: float
    speed: Optional[str] = None
    eta: Optional[str] = None
    filename: Optional[str] = None
    error_message: Optional[str] = None


class YouTubeDownloader:
    """Core YouTube downloader class using yt-dlp"""
    
    def __init__(self, download_path: str = "./downloads"):
        """
        Initialize the YouTube downloader
        
        Args:
            download_path: Directory where files will be downloaded
        """
        self.download_path = Path(download_path)
        self.download_path.mkdir(exist_ok=True)
        self.progress_callback: Optional[Callable[[DownloadProgress], None]] = None
        
    def set_progress_callback(self, callback: Callable[[DownloadProgress], None]):
        """Set a callback function to receive progress updates"""
        self.progress_callback = callback
    
    def _progress_hook(self, d: Dict[str, Any]):
        """Internal progress hook for yt-dlp"""
        if not self.progress_callback:
            return
            
        progress = DownloadProgress(
            status=d['status'],
            percentage=0.0
        )
        
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                progress.percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif '_percent_str' in d:
                # Extract percentage from string like "50.0%"
                percent_str = d['_percent_str'].strip().rstrip('%')
                try:
                    progress.percentage = float(percent_str)
                except (ValueError, AttributeError):
                    progress.percentage = 0.0
            
            progress.speed = d.get('_speed_str', None)
            progress.eta = d.get('_eta_str', None)
            progress.filename = d.get('filename', None)
            
        elif d['status'] == 'finished':
            progress.percentage = 100.0
            progress.filename = d.get('filename', None)
            
        elif d['status'] == 'error':
            progress.error_message = str(d.get('error', 'Unknown error'))
            
        self.progress_callback(progress)
    
    def get_video_info(self, url: str) -> VideoInfo:
        """
        Extract video information without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            VideoInfo object containing video metadata
            
        Raises:
            Exception: If video information cannot be extracted
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Handle playlist/channel URLs - get first video for info
                if 'entries' in info:
                    if info['entries']:
                        info = info['entries'][0]
                    else:
                        raise Exception("No videos found in playlist/channel")
                
                return VideoInfo(
                    id=info.get('id', ''),
                    title=info.get('title', 'Unknown Title'),
                    description=info.get('description', ''),
                    duration=info.get('duration', 0),
                    uploader=info.get('uploader', 'Unknown'),
                    upload_date=info.get('upload_date', ''),
                    view_count=info.get('view_count', 0),
                    thumbnail=info.get('thumbnail', ''),
                    formats=[
                        {
                            'format_id': f.get('format_id', ''),
                            'ext': f.get('ext', ''),
                            'quality': f.get('quality', ''),
                            'filesize': f.get('filesize', 0),
                            'format_note': f.get('format_note', '')
                        }
                        for f in info.get('formats', [])
                    ],
                    url=url
                )
                
        except Exception as e:
            raise Exception(f"Failed to extract video info: {str(e)}")
    
    def get_playlist_info(self, url: str) -> List[VideoInfo]:
        """
        Extract information from a playlist or channel
        
        Args:
            url: YouTube playlist or channel URL
            
        Returns:
            List of VideoInfo objects
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Only extract basic info for speed
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' not in info:
                    # Single video, return as list
                    return [self.get_video_info(url)]
                
                videos = []
                for entry in info['entries']:
                    if entry:
                        # Create basic VideoInfo from playlist entry
                        video_info = VideoInfo(
                            id=entry.get('id', ''),
                            title=entry.get('title', 'Unknown Title'),
                            description='',  # Not available in flat extraction
                            duration=entry.get('duration', 0),
                            uploader=entry.get('uploader', 'Unknown'),
                            upload_date='',
                            view_count=0,
                            thumbnail=entry.get('thumbnail', ''),
                            formats=[],
                            url=f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                        )
                        videos.append(video_info)
                
                return videos
                
        except Exception as e:
            raise Exception(f"Failed to extract playlist info: {str(e)}")
    
    def download_video(self, url: str, format_choice: DownloadFormat = DownloadFormat.MP4_BEST, 
                      output_filename: Optional[str] = None) -> str:
        """
        Download a video from YouTube
        
        Args:
            url: YouTube video URL
            format_choice: Video quality/format to download
            output_filename: Custom filename (optional)
            
        Returns:
            Path to the downloaded file
            
        Raises:
            Exception: If download fails
        """
        # Set up output template
        if output_filename:
            output_template = str(self.download_path / output_filename)
        else:
            output_template = str(self.download_path / "%(title)s.%(ext)s")
        
        ydl_opts = {
            'format': format_choice.value,
            'outtmpl': output_template,
            'progress_hooks': [self._progress_hook],
        }
        
        # Special handling for audio-only downloads
        if format_choice in [DownloadFormat.MP3_BEST, DownloadFormat.AUDIO_ONLY]:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
                # Get the actual filename of the downloaded file
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                
                # Construct expected filename
                if output_filename:
                    expected_file = self.download_path / output_filename
                else:
                    title = info.get('title', 'video')
                    # Clean title for filename
                    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                    if format_choice in [DownloadFormat.MP3_BEST, DownloadFormat.AUDIO_ONLY]:
                        expected_file = self.download_path / f"{clean_title}.mp3"
                    else:
                        expected_file = self.download_path / f"{clean_title}.mp4"
                
                return str(expected_file)
                
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if URL is a valid YouTube URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
                return True
        except:
            return False
    
    def get_supported_sites(self) -> List[str]:
        """Get list of supported sites from yt-dlp"""
        return list(yt_dlp.extractor.gen_extractor_classes())


# Factory function for easy instantiation
def create_downloader(download_path: str = "./downloads") -> YouTubeDownloader:
    """
    Factory function to create a YouTubeDownloader instance
    
    Args:
        download_path: Directory where files will be downloaded
        
    Returns:
        YouTubeDownloader instance
    """
    return YouTubeDownloader(download_path)