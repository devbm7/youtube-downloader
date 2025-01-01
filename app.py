import gradio as gr
import yt_dlp as youtube_dl
import os

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
            return f"Download successful: {title}"
    except Exception as e:
        return f"Error: {e}"

# Gradio Interface
def gradio_download(video_url):
    return download_video(video_url)

# Create Gradio Interface
interface = gr.Interface(
    fn=gradio_download,
    inputs=gr.Textbox(label="YouTube Video URL"),
    outputs=gr.Textbox(label="Download Status"),
    title="YouTube Video Downloader",
    description="Enter a YouTube URL to download the video."
)

# Launch the Gradio app
if __name__ == '__main__':
    interface.launch()
