"""Application configuration via environment variables and .env file."""

from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SmartFlow AI Bot configuration.

    All settings can be overridden via environment variables or a `.env` file.
    """

    # --- Telegram ---
    bot_token: SecretStr = Field(..., description="Telegram Bot API token from @BotFather")

    # --- LLM ---
    gemini_api_key: Optional[SecretStr] = Field(None, description="Google Gemini API key")
    openai_api_key: Optional[SecretStr] = Field(None, description="OpenAI API key (optional)")
    groq_api_key: Optional[SecretStr] = Field(None, description="Groq API key (optional)")
    llm_model: str = Field("gemini/gemini-3-flash-preview", description="LiteLLM model identifier")
    system_prompt: str = Field(
        "You are SmartFlow AI, a helpful and friendly Telegram assistant. "
        "Respond naturally and conversationally, like a knowledgeable friend. "
        "IMPORTANT: Do NOT use any markdown formatting — no asterisks, no bold, "
        "no headers, no bullet points with special symbols, no backticks. "
        "Write in plain text only. Use simple numbered lists or dashes if needed. "
        "Be concise and to the point.",
        description="System prompt for the LLM",
    )

    # --- Embeddings & RAG ---
    embedding_model: str = Field("models/gemini-embedding-2-preview", description="Embedding model name")
    rag_collection: str = Field("smartflow_docs", description="Qdrant collection name")
    rag_vector_size: int = Field(3072, description="Embedding vector dimension")
    rag_chunk_size: int = Field(1000, description="Text splitter chunk size")
    rag_chunk_overlap: int = Field(200, description="Text splitter chunk overlap")
    rag_top_k: int = Field(3, description="Number of documents to retrieve")

    # --- Voice ---
    whisper_model: str = Field("medium", description="Whisper model size: tiny/small/medium/large")
    whisper_device: str = Field("cpu", description="Whisper device: cpu/cuda")
    whisper_compute: str = Field("int8", description="Whisper compute type: int8/float16/float32")
    tts_voice: str = Field("ru-RU-SvetlanaNeural", description="Edge-TTS voice identifier")
    voice_use_rag: bool = Field(True, description="Use RAG retrieval for transcribed voice messages")
    max_document_size_mb: int = Field(20, description="Maximum uploaded document size in megabytes")
    max_chunks_per_document: int = Field(100, description="Maximum chunks created from one document")
    max_documents_per_chat: int = Field(20, description="Maximum indexed documents per user per chat")

    # --- Infrastructure ---
    redis_url: str = Field("redis://localhost:6379/0", description="Redis connection URL")
    qdrant_url: str = Field("http://localhost:6333", description="Qdrant connection URL")
    memory_ttl: int = Field(86400, description="Conversation memory TTL in seconds (24h)")
    max_history: int = Field(15, description="Max conversation exchanges to keep")
    data_dir: Path = Field(Path("data"), description="Directory for temporary files")

    # --- Webhook ---
    use_webhook: bool = Field(False, description="Use webhook mode instead of polling")
    webhook_url: Optional[str] = Field(None, description="Public webhook URL")
    webhook_path: str = Field("/webhook", description="Webhook endpoint path")
    port: int = Field(8000, description="Server port for webhook mode")

    @property
    def max_document_size_bytes(self) -> int:
        """Return the maximum supported document size in bytes."""
        return self.max_document_size_mb * 1024 * 1024

    @field_validator("webhook_path")
    @classmethod
    def normalize_webhook_path(cls, value: str) -> str:
        """Ensure webhook paths are consistently absolute."""
        if not value:
            return "/webhook"
        return value if value.startswith("/") else f"/{value}"

    @field_validator("data_dir", mode="before")
    @classmethod
    def normalize_data_dir(cls, value: str | Path) -> Path:
        """Expand user home in data directory paths."""
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        return path

    @model_validator(mode="after")
    def validate_runtime_requirements(self) -> "Settings":
        """Fail fast on invalid provider and webhook combinations."""
        model_name = self.llm_model.lower()

        if model_name.startswith("gemini/") and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini models.")
        if model_name.startswith("openai/") and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI models.")
        if model_name.startswith("groq/") and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for Groq models.")
        if "gemini" in self.embedding_model.lower() and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini embeddings.")
        if self.use_webhook and not self.webhook_url:
            raise ValueError("WEBHOOK_URL is required when USE_WEBHOOK=true.")
        return self

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent / ".env",
        env_file_encoding="utf-8",
    )


config = Settings()
