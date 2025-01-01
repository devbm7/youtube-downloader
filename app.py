from flask import Flask, request, render_template, jsonify
import yt_dlp as youtube_dl
import os

app = Flask(__name__)

# Function to download video
def download_video(video_url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return "Download successful"
    except Exception as e:
        return f"Error: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form.get('video_url')
    if not video_url:
        return jsonify({'status': 'fail', 'message': 'No URL provided.'})
    
    # Ensure downloads directory exists
    os.makedirs('downloads', exist_ok=True)

    result = download_video(video_url)
    return jsonify({'status': 'success', 'message': result})

if __name__ == '__main__':
    app.run(debug=True)
