# AI Video Assistant

An intelligent web application that transcribes YouTube videos or local media files, generates professional summaries and metadata, and provides an interactive RAG (Retrieval-Augmented Generation) chat engine to answer questions about your meetings or presentations.

Built using **Streamlit**, **LangChain**, **Chroma DB (in-memory)**, **OpenAI Whisper (local)**, and **Mistral AI**.

---

## Features

- **Local & YouTube Inputs**: Paste any YouTube link or enter a local file path (`.mp4`, `.mp3`, etc.).
- **Automatic Audio Processing**: Automatically extracts audio, normalizes parameters, and converts to WAV format.
- **Local Speech-to-Text**: Transcribes audio chunks using OpenAI's **Whisper** model running locally on your device.
- **Meeting Intelligence Extraction**:
  -  High-level structured bullet-point summary.
  -  Clear Action Items checklist.
  -  Key Decisions log.
  -  Open Questions list.
- **Interactive RAG Chat**: Chat directly with your meeting transcript. Uses an in-memory vector database for secure, transient, and lock-free session contexts.
- **Premium Maximalist UI**: Redesigned with a modern Neobrutalist design language featuring bold purple/pink accents, solid borders, and tactile shadows.

---

## Screenshots

<img width="1356" height="728" alt="image" src="https://github.com/user-attachments/assets/e811a554-f08b-46ea-a0d9-9a39955a168b" />
<img width="1360" height="727" alt="image" src="https://github.com/user-attachments/assets/7f510876-9ee3-4f8c-bf8f-4045a5b23eda" />


##  Quick Start (Local Setup)

### Prerequisites
Make sure you have Python 3.10 to 3.12 installed on your system.

### Step 1: Clone the Repository
```bash
git clone https://github.com/mohammadzameerp/AI-Video-Agent.git
cd AI-Video-Agent
```

### Step 2: Set Up Virtual Environment & Dependencies
We recommend setting up a virtual environment:
```bash
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on macOS/Linux:
source .venv/bin/activate

# Install required packages
pip install -r Requirements.txt
```

### Step 3: Install FFmpeg
The audio processor requires FFmpeg to convert media files:
* **Windows** (via winget): `winget install Gyan.FFmpeg`
* **macOS** (via homebrew): `brew install ffmpeg`
* **Linux** (via apt): `sudo apt-get install ffmpeg`

### Step 4: Configure Environment Variables
Create a file named `.env` in the root directory and add your Mistral API Key:
```env
MISTRAL_API_KEY=your_mistral_api_key_here
WHISPER_MODEL=small
```

---

## 🚀 Running the App

### Web Dashboard (Streamlit)
To start the interactive web application, run:
```bash
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

### Command Line Interface (CLI)
To run the analysis pipeline directly inside your terminal, run:
```bash
python main.py
```

---

