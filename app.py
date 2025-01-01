import gradio as gr
import yt_dlp as youtube_dl
import os
from urllib.parse import quote

# Base URL for file download (modify if hosting publicly)
BASE_URL = "http://127.0.0.1:7860/file/"

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
            filename = ydl.prepare_filename(result)
            file_path = os.path.abspath(filename)
            download_link = BASE_URL + quote(os.path.relpath(file_path, "downloads"))
            return f"Download successful: [Click here to download]({download_link})"
    except Exception as e:
        return f"Error: {e}"

# Gradio Interface
def gradio_download(video_url):
    return download_video(video_url)

# Serve files using Gradio
interface = gr.Interface(
    fn=gradio_download,
    inputs=gr.Textbox(label="YouTube Video URL"),
    outputs=gr.Markdown(label="Download Link"),
    title="YouTube Video Downloader",
    description="Enter a YouTube URL to download the video. Click the link to save the video to your device."
)

# Launch the Gradio app
if __name__ == '__main__':
    interface.launch(share=True)
