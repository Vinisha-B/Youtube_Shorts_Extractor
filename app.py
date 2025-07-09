from flask import Flask, render_template, request
import os
import json
import shutil
import webbrowser
import spacy
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Folders
UPLOAD_FOLDER = 'uploads'
SHORTS_FOLDER = 'shorts'
STATIC_SHORTS_FOLDER = os.path.join('static', 'shorts')
TRANSCRIPT_FILE = 'whisper_transcript.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SHORTS_FOLDER, exist_ok=True)
os.makedirs(STATIC_SHORTS_FOLDER, exist_ok=True)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "❌ No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "❌ No selected file", 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    extract_smart_clips(filepath)

    for clip in os.listdir(SHORTS_FOLDER):
        if clip.endswith(".mp4"):
            shutil.copy(os.path.join(SHORTS_FOLDER, clip), os.path.join(STATIC_SHORTS_FOLDER, clip))

    shorts = [f"shorts/{clip}" for clip in sorted(os.listdir(STATIC_SHORTS_FOLDER)) if clip.endswith(".mp4")]
    return render_template("results.html", shorts=shorts)

def extract_smart_clips(video_path):
    try:
        with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Transcript JSON not found")
        return

    segments = data.get("segments", [])
    if not segments:
        print("❌ No segments found in transcript")
        return

    doc = nlp(data["text"])
    highlight_keywords = ["why", "important", "discovered", "scientific", "found", "researchers", "experiment", "dream", "REM", "lucid", "theory", "explained"]

    highlight_sentences = [sent for sent in doc.sents if any(kw in sent.text.lower() for kw in highlight_keywords)]

    count = 0
    used_ids = set()

    for sentence in highlight_sentences:
        for segment in segments:
            if segment["id"] in used_ids:
                continue
            if sentence.text.strip() in segment["text"]:
                start = max(0, segment["start"])
                end = segment["end"]
                try:
                    clip = VideoFileClip(video_path).subclip(start, end)
                    clip_name = f"clip_{count+1}.mp4"
                    clip.write_videofile(os.path.join(SHORTS_FOLDER, clip_name), codec="libx264")
                    used_ids.add(segment["id"])
                    count += 1
                except Exception as e:
                    print("❌ Error creating clip:", e)
                break

    print(f"✅ Created {count} smart clips.")

if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)
