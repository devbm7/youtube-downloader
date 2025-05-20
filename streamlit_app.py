import streamlit as st
import os
import time
from pathlib import Path
import tempfile
from api import YouTubeDownloader, DownloadFormat, VideoInfo, DownloadProgress

# Page configuration
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="📹",
    layout="wide"
)

# Initialize session state
if 'downloader' not in st.session_state:
    # Create downloads directory in temp folder for demo
    downloads_dir = Path(tempfile.gettempdir()) / "youtube_downloads"
    st.session_state.downloader = YouTubeDownloader(str(downloads_dir))
    st.session_state.download_progress = None
    st.session_state.video_info = None
    st.session_state.is_downloading = False

def progress_callback(progress: DownloadProgress):
    """Callback function to update progress in session state"""
    st.session_state.download_progress = progress

# Set up progress callback
st.session_state.downloader.set_progress_callback(progress_callback)

# Main header
st.title("📹 YouTube Video Downloader")
st.markdown("Download videos from YouTube with ease!")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Format selection
    format_options = {
        "MP4 - Best Quality": DownloadFormat.MP4_BEST,
        "MP4 - 720p": DownloadFormat.MP4_720P,
        "MP4 - 480p": DownloadFormat.MP4_480P,
        "MP3 - Audio Only": DownloadFormat.MP3_BEST,
    }
    
    selected_format = st.selectbox(
        "Choose format:",
        options=list(format_options.keys()),
        index=0
    )
    
    # Download location info
    st.info(f"📁 Downloads will be saved to:\n`{st.session_state.downloader.download_path}`")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📎 Enter YouTube URL")
    
    # URL input
    url_input = st.text_input(
        "Paste YouTube URL here:",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Supports single videos, playlists, and channels"
    )
    
    # Action buttons
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🔍 Get Info", disabled=not url_input):
            if url_input:
                try:
                    with st.spinner("Extracting video information..."):
                        if "playlist" in url_input or "channel" in url_input:
                            # Handle playlist/channel
                            playlist_info = st.session_state.downloader.get_playlist_info(url_input)
                            st.session_state.video_info = playlist_info
                            st.success(f"Found {len(playlist_info)} videos!")
                        else:
                            # Handle single video
                            video_info = st.session_state.downloader.get_video_info(url_input)
                            st.session_state.video_info = [video_info]
                            st.success("Video information extracted!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col_btn2:
        if st.button("⬬ Download", disabled=not url_input or st.session_state.is_downloading):
            if url_input:
                st.session_state.is_downloading = True
                st.session_state.download_progress = None
                
                try:
                    format_choice = format_options[selected_format]
                    
                    with st.spinner("Starting download..."):
                        downloaded_file = st.session_state.downloader.download_video(
                            url_input, 
                            format_choice
                        )
                    
                    st.success(f"✅ Download completed!\nFile: {downloaded_file}")
                    
                except Exception as e:
                    st.error(f"Download failed: {str(e)}")
                finally:
                    st.session_state.is_downloading = False
    
    with col_btn3:
        if st.button("🗑️ Clear"):
            st.session_state.video_info = None
            st.session_state.download_progress = None
            url_input = ""
            st.rerun()

# Progress display
if st.session_state.is_downloading and st.session_state.download_progress:
    progress = st.session_state.download_progress
    
    if progress.status == "downloading":
        st.header("⬬ Download Progress")
        
        # Progress bar
        progress_bar = st.progress(progress.percentage / 100)
        
        # Progress info
        col_prog1, col_prog2, col_prog3 = st.columns(3)
        with col_prog1:
            st.metric("Progress", f"{progress.percentage:.1f}%")
        with col_prog2:
            if progress.speed:
                st.metric("Speed", progress.speed)
        with col_prog3:
            if progress.eta:
                st.metric("ETA", progress.eta)
        
        if progress.filename:
            st.text(f"Downloading: {Path(progress.filename).name}")
    
    elif progress.status == "finished":
        st.success("✅ Download completed!")
        st.session_state.is_downloading = False
    
    elif progress.status == "error":
        st.error(f"❌ Download failed: {progress.error_message}")
        st.session_state.is_downloading = False

with col2:
    # Video information display
    if st.session_state.video_info:
        st.header("📋 Video Information")
        
        if len(st.session_state.video_info) == 1:
            # Single video
            video = st.session_state.video_info[0]
            
            if video.thumbnail:
                st.image(video.thumbnail, width=300)
            
            st.subheader(video.title)
            st.text(f"👤 {video.uploader}")
            
            if video.duration:
                minutes = video.duration // 60
                seconds = video.duration % 60
                st.text(f"⏱️ {minutes}:{seconds:02d}")
            
            if video.view_count:
                st.text(f"👁️ {video.view_count:,} views")
            
            if video.description:
                with st.expander("📝 Description"):
                    st.text(video.description[:500] + "..." if len(video.description) > 500 else video.description)
        
        else:
            # Playlist/Channel
            st.subheader(f"📋 Playlist ({len(st.session_state.video_info)} videos)")
            
            for i, video in enumerate(st.session_state.video_info[:10]):  # Show first 10
                with st.expander(f"{i+1}. {video.title}"):
                    col_thumb, col_info = st.columns([1, 2])
                    
                    with col_thumb:
                        if video.thumbnail:
                            st.image(video.thumbnail, width=120)
                    
                    with col_info:
                        st.text(f"👤 {video.uploader}")
                        if video.duration:
                            minutes = video.duration // 60
                            seconds = video.duration % 60
                            st.text(f"⏱️ {minutes}:{seconds:02d}")
            
            if len(st.session_state.video_info) > 10:
                st.text(f"... and {len(st.session_state.video_info) - 10} more videos")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    <p>🚀 Powered by yt-dlp | Built with Streamlit</p>
    <p>⚠️ Please respect copyright laws and YouTube's Terms of Service</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Auto-refresh for progress updates
if st.session_state.is_downloading:
    time.sleep(0.5)
    st.rerun()