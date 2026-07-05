import os
import re
import shutil

# Dynamic FFmpeg PATH resolution for local Windows development only.
# On Linux (Streamlit Cloud), ffmpeg is installed via packages.txt and found automatically.
ffmpeg_dir = r"C:\Users\zebat\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
if os.name == "nt" and not shutil.which("ffmpeg") and os.path.exists(ffmpeg_dir):
    os.environ["PATH"] += os.pathsep + ffmpeg_dir

import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ── YouTube Transcript (primary path for YouTube URLs) ─────────────────────────

def _extract_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from any YouTube URL format."""
    patterns = [
        r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_youtube_transcript(url: str) -> str | None:
    """
    Fetch transcript directly from YouTube's caption API.
    This works from any IP (including cloud datacenter IPs) and requires
    no audio download, no FFmpeg, and no Whisper inference.
    Returns the transcript text, or None if captions are unavailable.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        video_id = _extract_video_id(url)
        if not video_id:
            return None

        # Prefer manually-written English captions, fall back to auto-generated
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except Exception:
            pass

        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except Exception:
                pass

        if transcript is None:
            # Try any available transcript and translate it to English
            try:
                transcript = transcript_list.find_generated_transcript(
                    [t.language_code for t in transcript_list]
                ).translate("en")
            except Exception:
                return None

        entries = transcript.fetch()
        text = " ".join(entry["text"] for entry in entries)
        print(f"✅ YouTube transcript fetched directly ({len(text)} characters).")
        return text

    except Exception as e:
        print(f"⚠️ YouTube transcript API failed ({e}). Will try audio download.")
        return None


# ── YouTube Audio Download (fallback for videos without captions) ──────────────

def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL using yt-dlp.
    Tries android → ios → web player clients to bypass 403 blocks.
    """
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    player_clients = ["android", "ios", "web"]

    base_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.6261.119 Mobile Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    last_error = None
    for client in player_clients:
        opts = {**base_opts, "extractor_args": {"youtube": {"player_client": [client]}}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = (
                    ydl.prepare_filename(info)
                    .replace(".webm", ".wav")
                    .replace(".m4a", ".wav")
                    .replace(".opus", ".wav")
                )
            print(f"✅ Audio download succeeded using player client: {client}")
            return filename
        except Exception as e:
            print(f"⚠️ Player client '{client}' failed: {e}. Trying next...")
            last_error = e

    raise RuntimeError(
        f"All player clients failed to download the video. Last error: {last_error}"
    )


# ── Local File Conversion ──────────────────────────────────────────────────────

def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # 16kHz mono
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


# ── Main Entry Point ───────────────────────────────────────────────────────────

def process_input(source: str):
    """
    Process a YouTube URL or local file path.

    Returns:
      - str:  pre-fetched transcript text (YouTube with captions) — skip Whisper
      - list: audio chunk file paths (local files or YouTube without captions) — use Whisper
    """
    source = source.strip().strip("'\"")

    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL.")

        # Primary path: fetch transcript directly (fast, no 403 issues)
        transcript_text = fetch_youtube_transcript(source)
        if transcript_text:
            return transcript_text  # ← returns str, caller skips Whisper

        # Fallback path: download audio + run Whisper
        print("Falling back to audio download + Whisper transcription...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks  # ← returns list, caller runs Whisper
