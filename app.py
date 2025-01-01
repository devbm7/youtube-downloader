import streamlit as st
import yt_dlp as youtube_dl
import os
from pathlib import Path
from PIL import Image
from io import BytesIO
import requests

# Function to fetch video details and formats
def fetch_video_details(video_url):
    ydl_opts = {'quiet': True}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        formats = [
            {
                "format_id": f["format_id"],
                "ext": f["ext"],
                "resolution": f.get("resolution", "audio only" if "audio" in f["format"] else "unknown"),
                "filesize": f.get("filesize", None)
            }
            for f in info["formats"] if f.get("format_id") and f.get("ext")
        ]
        return {
            "title": info["title"],
            "thumbnail": info["thumbnail"],
            "formats": formats
        }

# Function to download video with progress
def download_video(video_url, format_id, progress_callback):
    ydl_opts = {
        'format': format_id,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'progress_hooks': [progress_callback],
    }
    try:
        os.makedirs('downloads', exist_ok=True)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=True)
            title = result.get('title', 'Unknown Title')
            filepath = Path(ydl.prepare_filename(result)).resolve()
            return f"Download successful: {title}", filepath
    except Exception as e:
        return f"Error: {e}", None

# Streamlit app
st.title("Enhanced YouTube Video Downloader")
st.write("Enter a YouTube URL to preview and download the video in your desired quality.")

# Input field for video URL
video_url = st.text_input("YouTube Video URL:")

if video_url.strip():
    with st.spinner("Fetching video details..."):
        try:
            details = fetch_video_details(video_url)
            st.success(f"Video found: {details['title']}")

            # Display thumbnail
            response = requests.get(details['thumbnail'])
            thumbnail = Image.open(BytesIO(response.content))
            st.image(thumbnail, caption=details['title'], use_column_width=True)

            # Dropdown for format selection
            format_options = [
                f"{f['resolution']} ({f['ext']}) - {f['filesize'] or 'Unknown size'} bytes"
                for f in details['formats']
            ]
            selected_format = st.selectbox("Select Format:", options=format_options, index=0)

            # Extract selected format_id
            selected_format_id = details['formats'][format_options.index(selected_format)]["format_id"]

            # Progress bar
            progress = st.progress(0)

            def progress_hook(d):
                if d['status'] == 'downloading':
                    total_bytes = d.get('total_bytes', 1)
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    progress.progress(downloaded_bytes / total_bytes)

            if st.button("Download"):
                with st.spinner("Downloading..."):
                    status, filepath = download_video(video_url, selected_format_id, progress_hook)
                    if filepath:
                        st.success(status)
                        with open(filepath, "rb") as f:
                            st.download_button(
                                label="Download Video",
                                data=f,
                                file_name=filepath.name,
                                mime=f"video/{filepath.suffix.lstrip('.')}"
                            )
                    else:
                        st.error(status)
        except Exception as e:
            st.error(f"Error fetching video details: {e}")
