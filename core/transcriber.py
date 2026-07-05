import os
from faster_whisper import WhisperModel

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

_model = None

def load_model():
    global _model
    if _model is None:
        print(f"Loading faster-whisper model: {WHISPER_MODEL} ...")
        # Use CPU with int8 quantization — works on Streamlit Cloud free tier (no GPU)
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        print("faster-whisper model loaded.")
    return _model

def transcribe_chunk_whisper(chunk_path: str) -> str:
    model = load_model()
    segments, _ = model.transcribe(chunk_path, task="transcribe")
    return " ".join(segment.text for segment in segments)

def transcribe_chunk(chunk_path: str) -> str:
    """Transcribe one audio chunk using faster-whisper."""
    return transcribe_chunk_whisper(chunk_path)

def transcribe_all(chunks: list) -> str:
    full_transcript = ""
    print("Using faster-whisper for transcription.")

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk)
        full_transcript += text + " "

    print("Transcription complete.")
    return full_transcript.strip()
