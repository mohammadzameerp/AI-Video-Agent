import os
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


def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL using yt-dlp.
    Tries multiple player clients in order to bypass HTTP 403 blocks
    that YouTube enforces on cloud/datacenter IP addresses.
    """
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    # Player clients to try in order.
    # "android" and "ios" bypass the 403 blocks on cloud server IPs.
    # "web" is kept as final fallback.
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
        opts = {
            **base_opts,
            "extractor_args": {"youtube": {"player_client": [client]}},
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = (
                    ydl.prepare_filename(info)
                    .replace(".webm", ".wav")
                    .replace(".m4a", ".wav")
                    .replace(".opus", ".wav")
                )
            print(f"Download succeeded using player client: {client}")
            return filename
        except Exception as e:
            print(f"Player client '{client}' failed: {e}. Trying next...")
            last_error = e

    raise RuntimeError(
        f"All player clients failed to download the video. Last error: {last_error}"
    )


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


def process_input(source: str) -> list:
    source = source.strip().strip("'\"")
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
