# SmartFlow AI

A powerful, production-ready Telegram Assistant Bot built with aiogram 3.x, litellm, fastAPI, Qdrant, Redis, faster-whisper, and edge-tts.

## Features
- **Conversational Memory**: Backed by Redis, remembering the last 15 exchanges.
- **RAG via Documents**: Upload PDF/DOCX/TXT files to index them in Qdrant and chat with your documents.
- **Voice Messages**: STT via `faster-whisper` and TTS via `edge-tts`.
- **LLM Routing**: `litellm` integration supports OpenAI, Groq, Gemini under the hood.
- **Webhook vs Polling**: Easily switch between local polling and production webhooks via `.env`.

## Requirements
- Python 3.11+
- `ffmpeg` installed on your system (for audio processing via `pydub` and `faster-whisper`)
- Redis server
- Qdrant (local or cloud)

## Setup
1. Clone the repository and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Make sure system dependencies are installed:
   ```bash
   sudo apt install ffmpeg
   ```

3. Copy the env file and configure your keys:
   ```bash
   cp .env.example .env
   # Edit .env and supply bot token, api keys, and URLs
   ```

## Running the Bot

**For Development (Polling):**
Set `USE_WEBHOOK=false` in `.env`.
```bash
python main.py
```

**For Production (Webhook via FastAPI):**
Set `USE_WEBHOOK=true` and provide `WEBHOOK_URL` in `.env`.
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```
