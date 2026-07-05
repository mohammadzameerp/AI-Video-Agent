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

# Detect whether the app is running on Streamlit Cloud (Linux /mount/src path)
IS_CLOUD = os.path.exists("/mount/src")


# ── YouTube Transcript (primary path for all YouTube URLs) ─────────────────────

def _extract_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from any YouTube URL format."""
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else None


def fetch_youtube_transcript(url: str) -> str:
    """
    Fetch transcript directly from YouTube's caption API.
    Works from cloud datacenter IPs — no audio download required.
    Raises a user-friendly RuntimeError if captions are unavailable.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
    except ImportError:
        raise RuntimeError("youtube-transcript-api is not installed. Add it to requirements.txt.")

    video_id = _extract_video_id(url)
    if not video_id:
        raise RuntimeError(f"Could not extract a valid YouTube video ID from URL: {url}")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled:
        raise RuntimeError(
            "❌ This video has transcripts/captions **disabled** by the creator.\n\n"
            "**What to do:**\n"
            "- Try a different YouTube video that has auto-generated captions.\n"
            "- Or download the video to your device and upload the file directly."
        )
    except Exception as e:
        raise RuntimeError(
            f"❌ Could not fetch transcript for this video: {e}\n\n"
            "**What to do:**\n"
            "- Check that the YouTube URL is correct and the video is publicly accessible.\n"
            "- Try a video with auto-generated captions (most YouTube videos have these).\n"
            "- Or upload the video file directly."
        )

    # Try manually-created English captions first, then auto-generated, then translate
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
        try:
            # Any language → translate to English
            available = list(transcript_list)
            if available:
                transcript = available[0].translate("en")
        except Exception:
            pass

    if transcript is None:
        raise RuntimeError(
            "❌ No captions found for this video in any language.\n\n"
            "**What to do:**\n"
            "- YouTube Shorts and some videos do not have auto-generated captions.\n"
            "- Try a longer YouTube video (5+ minutes) which usually has captions.\n"
            "- Or download the video to your device and upload the file directly."
        )

    entries = transcript.fetch()
    # Handle both dict-style and object-style entries across API versions
    parts = []
    for entry in entries:
        if isinstance(entry, dict):
            parts.append(entry.get("text", ""))
        else:
            parts.append(getattr(entry, "text", str(entry)))

    text = " ".join(p for p in parts if p.strip())
    if not text.strip():
        raise RuntimeError(
            "❌ The captions for this video appear to be empty.\n\n"
            "Please try a different video or upload the file directly."
        )

    print(f"✅ YouTube transcript fetched ({len(text)} characters).")
    return text


# ── YouTube Audio Download (local-only fallback) ───────────────────────────────

def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL using yt-dlp.
    Only called when running locally (not on Streamlit Cloud).
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
            print(f"✅ Audio downloaded using player client: {client}")
            return filename
        except Exception as e:
            print(f"⚠️ Player client '{client}' failed: {e}. Trying next...")
            last_error = e

    raise RuntimeError(
        f"All player clients failed to download the video.\nLast error: {last_error}"
    )


# ── Local File Conversion ──────────────────────────────────────────────────────

def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
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


# ── Main Entry Point ───────────────────────────────────────────────────────────

def process_input(source: str):
    """
    Process a YouTube URL or local file path.

    For YouTube URLs:
      - ALWAYS uses youtube-transcript-api (works from any IP, no download needed).
      - On cloud: raises a clear error if captions are unavailable.
      - On local: falls back to yt-dlp audio download + Whisper if captions unavailable.

    Returns:
      - str:  pre-fetched transcript text → caller skips Whisper
      - list: audio chunk file paths → caller runs Whisper
    """
    source = source.strip().strip("'\"")

    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL.")

        if IS_CLOUD:
            # On cloud: only transcript API (yt-dlp will always fail from datacenter IPs)
            return fetch_youtube_transcript(source)  # raises clear error if no captions
        else:
            # On local: try transcript API first, fall back to audio download
            try:
                return fetch_youtube_transcript(source)
            except RuntimeError as e:
                print(f"Transcript API failed locally: {e}\nFalling back to audio download...")
                wav_path = download_youtube_audio(source)
                chunks = chunk_audio(wav_path)
                return chunks

    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)
        chunks = chunk_audio(wav_path)
        print(f"Audio ready — {len(chunks)} chunk(s) created.")
        return chunks
