from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional

class Settings(BaseSettings):
    bot_token: SecretStr
    openai_api_key: Optional[SecretStr] = None
    groq_api_key: Optional[SecretStr] = None
    gemini_api_key: Optional[SecretStr] = None
    
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    
    use_webhook: bool = False
    webhook_url: Optional[str] = None
    webhook_path: str = "/webhook"
    port: int = 8000
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Settings()
