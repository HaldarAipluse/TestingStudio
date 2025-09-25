from flask import Flask, request, send_file, render_template_string, after_this_request
import yt_dlp
import os
import re
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# HTML with Premium UI Background + Glassmorphism
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Premium YT Downloader</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
* {margin:0;padding:0;box-sizing:border-box;font-family:'Roboto',sans-serif;}
body {
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
    overflow:hidden;
    background: #0f2027;
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    position: relative;
}

/* Animated particles background */
body::before {
    content:"";
    position:absolute;
    top:0; left:0; width:100%; height:100%;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px);
    background-size: 50px 50px;
    animation: moveBg 20s linear infinite;
    z-index:0;
}
@keyframes moveBg {
    0% {background-position:0 0;}
    100% {background-position:1000px 1000px;}
}

/* Glassmorphic card */
.container {
    position: relative;
    backdrop-filter: blur(20px);
    background: rgba(255, 255, 255, 0.08);
    border-radius: 25px;
    padding: 50px 70px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    text-align: center;
    max-width: 450px;
    width: 90%;
    z-index:1;
    animation: floatCard 6s ease-in-out infinite, fadeIn 1.2s ease forwards;
}

/* Floating & Fade-in animations */
@keyframes fadeIn {0% {opacity:0; transform: translateY(-30px);} 100% {opacity:1; transform: translateY(0);}}
@keyframes floatCard {0% {transform: translateY(0);} 50% {transform: translateY(-15px);} 100% {transform: translateY(0);}}

h1 {
    color:#fff; 
    margin-bottom:35px; 
    text-shadow: 0 4px 20px rgba(0,0,0,0.3);
    animation: slideDown 1s ease forwards;
}
@keyframes slideDown {0% {opacity:0; transform: translateY(-20px);} 100% {opacity:1; transform: translateY(0);}}

input[type="text"] {
    width:100%; padding:18px; border-radius:20px; border:none; outline:none;
    font-size:16px; background: rgba(255,255,255,0.15); color:#fff; margin-bottom:25px;
    backdrop-filter: blur(12px); transition: all 0.3s ease; box-shadow: 0 4px 30px rgba(0,0,0,0.2);
}
input[type="text"]:focus {background: rgba(255,255,255,0.25); transform: scale(1.02);}

button {
    padding:18px 40px; border:none; border-radius:20px; 
    background: linear-gradient(135deg,#ff6ec7,#7873f5);
    color:#fff; font-size:16px; cursor:pointer; transition: all 0.3s ease;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}
button:hover {transform: translateY(-3px) scale(1.05); box-shadow:0 12px 40px rgba(0,0,0,0.5);}
button:active {transform: translateY(0) scale(1); box-shadow:0 8px 30px rgba(0,0,0,0.4);}
button.downloading {animation: pulse 1s infinite;}
@keyframes pulse {0% {transform: scale(1);} 50% {transform: scale(1.05);} 100% {transform: scale(1);}}

#status {
    margin-top:22px; color:#fff; font-weight:500; min-height:24px; animation: fadeIn 1s ease;
}
</style>
</head>
<body>
<div class="container">
    <h1>Premium YT Downloader</h1>
    <input type="text" id="url" placeholder="Enter YouTube URL" />
    <button id="downloadBtn" onclick="download()">Download</button>
    <p id="status"></p>
</div>

<script>
async function download() {
    const url = document.getElementById('url').value;
    const status = document.getElementById('status');
    const button = document.getElementById('downloadBtn');
    if(!url){ status.innerText = 'Please enter a URL'; return; }
    
    button.classList.add('downloading');
    status.innerText = 'Downloading...';

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url })
        });

        if(response.ok){
            const blob = await response.blob();
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'video.mp4';
            link.click();
            status.innerText = 'Download complete!';
        } else {
            const error = await response.text();
            status.innerText = 'Download failed: ' + error;
        }
    } catch(err){
        status.innerText = 'Error: ' + err;
    } finally { button.classList.remove('downloading'); }
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_content)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    if not url: return "No URL provided", 400

    # Validate YouTube URL
    if not re.match(r'https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)', url):
        return "Invalid YouTube URL", 400

    # Unique filename
    unique_id = str(uuid.uuid4())
    ydl_opts = {'format':'best', 'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'{unique_id}_%(title)s.%(ext)s')}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        @after_this_request
        def remove_file(response):
            try: os.remove(filename)
            except Exception as e: print("Error removing file:", e)
            return response

        return send_file(filename, as_attachment=True)
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=True)