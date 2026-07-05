import os
import re
import shutil
import tempfile

# Dynamic FFmpeg PATH resolution for local Windows development only.
ffmpeg_dir = r"C:\Users\zebat\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
if os.name == "nt" and not shutil.which("ffmpeg") and os.path.exists(ffmpeg_dir):
    os.environ["PATH"] += os.pathsep + ffmpeg_dir

import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Detect Streamlit Cloud environment
IS_CLOUD = os.path.exists("/mount/src")


# ── YouTube Transcript API ─────────────────────────────────────────────────────

def _extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


def fetch_youtube_transcript(url: str) -> str:
    """
    Fetch transcript directly from YouTube's caption API using get_transcript().
    Compatible with all versions of youtube-transcript-api.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError("youtube-transcript-api is not installed.")

    video_id = _extract_video_id(url)
    if not video_id:
        raise RuntimeError(f"Could not extract a valid YouTube video ID from: {url}")

    snippets = None
    last_error = None

    # Try English first, then any language
    for lang_args in [{"languages": ["en", "en-US", "en-GB"]}, {}]:
        try:
            snippets = YouTubeTranscriptApi.get_transcript(video_id, **lang_args)
            break
        except Exception as e:
            last_error = e

    if snippets is None:
        raise RuntimeError(
            f"❌ No captions found for this video.\n\n"
            f"**Details:** {last_error}\n\n"
            "**What to do:**\n"
            "- YouTube Shorts and some videos have no auto-generated captions.\n"
            "- Try a regular YouTube video (5+ min) — most have auto-captions.\n"
            "- Or use the **Upload File** tab to upload a video/audio file directly."
        )

    text = " ".join(
        s["text"] if isinstance(s, dict) else getattr(s, "text", str(s))
        for s in snippets
    )

    if not text.strip():
        raise RuntimeError(
            "❌ The captions for this video are empty.\n\n"
            "Please try a different video or use the **Upload File** tab."
        )

    print(f"✅ YouTube transcript fetched ({len(text)} characters).")
    return text


# ── YouTube Audio Download (local fallback only) ───────────────────────────────

def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    player_clients = ["android", "ios", "web"]
    base_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav", "preferredquality": "192"}],
        "quiet": True,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 Chrome/122.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    last_error = None
    for client in player_clients:
        try:
            opts = {**base_opts, "extractor_args": {"youtube": {"player_client": [client]}}}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                for ext in [".webm", ".m4a", ".opus"]:
                    filename = filename.replace(ext, ".wav")
            return filename
        except Exception as e:
            last_error = e
    raise RuntimeError(f"All player clients failed. Last error: {last_error}")


# ── File Conversion & Chunking ─────────────────────────────────────────────────

def convert_to_wav(input_path: str) -> str:
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks


# ── Uploaded File Entry Point ──────────────────────────────────────────────────

def process_uploaded_file(uploaded_file) -> list:
    """
    Accept a Streamlit UploadedFile object, save to a temp file,
    convert to WAV, chunk, and return chunk paths for Whisper transcription.
    """
    suffix = os.path.splitext(uploaded_file.name)[-1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=DOWNLOAD_DIR) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    print(f"File saved to {tmp_path}. Converting to WAV...")
    wav_path = convert_to_wav(tmp_path)
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks


# ── YouTube URL Entry Point ────────────────────────────────────────────────────

def process_input(source: str):
    """
    Process a YouTube URL or local file path.
    Returns str (pre-fetched transcript) or list (audio chunks for Whisper).
    """
    source = source.strip().strip("'\"")

    if source.startswith("http://") or source.startswith("https://"):
        if IS_CLOUD:
            # Cloud: only transcript API (yt-dlp always fails from datacenter IPs)
            return fetch_youtube_transcript(source)
        else:
            # Local: try transcript API, fall back to audio download
            try:
                return fetch_youtube_transcript(source)
            except RuntimeError as e:
                print(f"Transcript API failed: {e}\nFalling back to yt-dlp...")
                wav_path = download_youtube_audio(source)
                return chunk_audio(wav_path)
    else:
        print("Detected local file path. Converting to WAV...")
        wav_path = convert_to_wav(source)
        chunks = chunk_audio(wav_path)
        print(f"Audio ready — {len(chunks)} chunk(s) created.")
        return chunks
