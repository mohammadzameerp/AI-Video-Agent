# AI Video Assistant Deployment Guide

This document describes how to deploy the **AI Video Assistant** to the web so that anyone can access and use it.

---

## Recommended: Streamlit Community Cloud (Free & Easy)

Streamlit provides a free hosting service directly integrated with GitHub. It builds, dependency-resolves, and deploys your app instantly.

### Step 1: Push Code to GitHub
1. Make sure your complete project is pushed to your GitHub repository (e.g., `https://github.com/mohammadzameerp/AI-Video-Agent.git`).
2. Verify that `Requirements.txt` (for Python packages) and `packages.txt` (for the `ffmpeg` system binary) are present in the root folder.

### Step 2: Sign Up & Deploy on Streamlit Cloud
1. Go to [Streamlit Community Cloud](https://share.streamlit.io/) and click **Sign up**.
2. Connect your GitHub account.
3. Click **Create app** (or **New app**).
4. Fill in the deployment details:
   * **Repository**: Select `mohammadzameerp/AI-Video-Agent`
   * **Branch**: `main`
   * **Main file path**: `app.py`
5. Click **Advanced settings...** at the bottom:
   * Under the **Secrets** text area, paste your environment variables (especially your Mistral API key):
     ```toml
     MISTRAL_API_KEY = "your_actual_mistral_api_key_here"
     WHISPER_MODEL = "small"
     ```
   * Click **Save**.
6. Click **Deploy!**

Streamlit Cloud will automatically:
* Read `packages.txt` and install `ffmpeg` onto the Linux container.
* Install Python packages from `Requirements.txt`.
* Start your server and provide you with a public URL (e.g., `https://ai-video-agent.streamlit.app/`).

---

## Alternative 1: Deploying to Hugging Face Spaces (Free)

Hugging Face Spaces supports Streamlit applications natively:

1. Create a Hugging Face account and select **New Space**.
2. Set Space SDK to **Streamlit**.
3. Create a file named `packages.txt` in your repo with `ffmpeg` in it.
4. Upload all your files to the Hugging Face git repository.
5. Under Space Settings, add your environment variables as Secrets:
   * Key: `MISTRAL_API_KEY`
   * Value: `your_actual_key`
6. Hugging Face will build and host the app automatically.

---

## Alternative 2: Self-Hosting / Linux Server (VPS/Render/Docker)

If hosting on a Linux server, Docker, or Render:

### System Requirements (FFmpeg)
Ensure `ffmpeg` and `ffprobe` are installed on the host system:
* **Ubuntu/Debian**:
  ```bash
  sudo apt-get update
  sudo apt-get install -y ffmpeg
  ```
* **macOS** (Homebrew):
  ```bash
  brew install ffmpeg
  ```
* **CentOS/RHEL**:
  ```bash
  sudo yum install -y ffmpeg
  ```

### Run Server
Activate your virtual environment and start Streamlit:
```bash
python -m pip install -r Requirements.txt
python -m streamlit run app.py --server.port 8080 --server.address 0.0.0.0
```
