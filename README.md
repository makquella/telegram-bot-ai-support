# 🤖 SmartFlow AI

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4?logo=telegram&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A production-ready **AI-powered Telegram assistant** with conversational memory, document Q&A (RAG), voice messages, and multi-model LLM support.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **Smart Chat** | Context-aware conversations powered by Gemini / OpenAI / Groq via LiteLLM |
| 📄 **Document Q&A** | Upload PDF / DOCX / TXT → auto-indexed in Qdrant → ask questions about content |
| 🎙 **Voice Mode** | Send a voice message → STT (Whisper) → LLM → TTS (Edge-TTS) → voice reply |
| 🧠 **Memory** | Redis-backed conversation history with configurable TTL and max exchanges |
| ⚡ **Dual Mode** | Long-polling for development, FastAPI webhooks for production |
| 🐳 **Docker** | One-command deployment with `docker compose up` |

---

## 🏗 Architecture

```mermaid
graph LR
    U[Telegram User] -->|message| B[aiogram Bot]
    B --> CMD[Command Handler]
    B --> DOC[Document Handler]
    B --> VOI[Voice Handler]
    B --> CHT[Chat Handler]

    DOC -->|load & split| RAG[RAG Pipeline]
    RAG -->|embed| EMB[Gemini Embeddings]
    EMB -->|store| QD[(Qdrant)]

    CHT -->|retrieve context| QD
    CHT -->|generate| LLM[LiteLLM / Gemini]
    CHT -->|history| RD[(Redis)]

    VOI -->|transcribe| STT[Whisper]
    VOI -->|synthesize| TTS[Edge-TTS]
    VOI --> LLM
```

---

## 📁 Project Structure

```
smartflow-ai-bot/
├── main.py              # Polling entrypoint
├── app.py               # Webhook entrypoint (FastAPI)
├── config.py            # Pydantic-settings configuration
├── handlers/
│   ├── commands.py      # /start, /help, /clear, /status
│   ├── chat.py          # Text message handler with RAG
│   ├── voice.py         # Voice message pipeline (STT → LLM → TTS)
│   └── document.py      # File upload and indexing
├── utils/
│   ├── llm.py           # LiteLLM integration
│   └── audio.py         # Whisper STT + Edge-TTS
├── rag/
│   ├── embedder.py      # Gemini embedding model
│   ├── loader.py        # Document loading & chunking
│   ├── chain.py         # Context retrieval
│   └── vectorstore.py   # Qdrant vector store
├── memory/
│   └── conversation.py  # Redis conversation memory
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── LICENSE
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Redis & Qdrant)
- `ffmpeg` (for voice processing)
- Gemini API key ([get one free](https://aistudio.google.com/))

### 1. Clone & Install

```bash
git clone https://github.com/makquella/telegram-bot-ai-support.git
cd telegram-bot-ai-support
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set BOT_TOKEN and GEMINI_API_KEY at minimum
```

### 3. Start Services

```bash
# Redis + Qdrant
docker run -d --name redis -p 6379:6379 redis:7-alpine
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
```

### 4. Run

```bash
python main.py
```

---

## 🐳 Docker Deployment

Full-stack deployment with a single command:

```bash
cp .env.example .env
# Edit .env with your tokens
docker compose up -d
```

This starts the bot, Redis, and Qdrant with persistent storage.

---

## ⚙️ Configuration

All settings via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | — | Telegram bot token (required) |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `LLM_MODEL` | `gemini/gemini-3-flash-preview` | LiteLLM model ID |
| `EMBEDDING_MODEL` | `models/gemini-embedding-2-preview` | Embedding model |
| `WHISPER_MODEL` | `medium` | Whisper size: tiny/small/medium/large |
| `TTS_VOICE` | `ru-RU-SvetlanaNeural` | Edge-TTS voice |
| `MAX_HISTORY` | `15` | Conversation exchanges to remember |
| `MEMORY_TTL` | `86400` | Memory auto-expiry (seconds) |

See [.env.example](.env.example) for the full list.

---

## 🛠 Tech Stack

- **Bot Framework**: [aiogram 3.x](https://docs.aiogram.dev/)
- **LLM**: [LiteLLM](https://github.com/BerriAI/litellm) (Gemini, OpenAI, Groq)
- **Embeddings**: [Google Gemini Embedding](https://ai.google.dev/gemini-api/docs/embeddings)
- **Vector Store**: [Qdrant](https://qdrant.tech/)
- **Memory**: [Redis](https://redis.io/)
- **STT**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- **TTS**: [edge-tts](https://github.com/rany2/edge-tts)
- **Webhook**: [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/)
- **Config**: [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## 📝 License

[MIT](LICENSE)
