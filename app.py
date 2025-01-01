import streamlit as st
import yt_dlp as youtube_dl
import os
from pathlib import Path

# Function to download video
def download_video(video_url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }
    try:
        # Ensure downloads directory exists
        os.makedirs('downloads', exist_ok=True)
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=True)
            title = result.get('title', 'Unknown Title')
            filepath = ydl.prepare_filename(result)
            filepath = Path(filepath).resolve()
            return f"Download successful: {title}", filepath
    except Exception as e:
        return f"Error: {e}", None

# Streamlit app
st.title("YouTube Video Downloader")
st.write("Enter a YouTube URL to download the video.")

# Input field for video URL
video_url = st.text_input("YouTube Video URL:")

if st.button("Download"):
    if not video_url.strip():
        st.error("Please enter a valid YouTube URL.")
    else:
        status, filepath = download_video(video_url)
        if filepath:
            st.success(status)
            with open(filepath, "rb") as f:
                btn = st.download_button(
                    label="Download Video",
                    data=f,
                    file_name=filepath.name,
                    mime="video/mp4"
                )
        else:
            st.error(status)
