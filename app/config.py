"""Application configuration management."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://rpgai:rpgai_password@localhost:5432/rpgai"
    DATABASE_USER: str = "rpgai"
    DATABASE_PASSWORD: str = "rpgai_password"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: str = "5432"
    DATABASE_NAME: str = "rpgai"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # LLM Providers
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "granite4:micro"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"
    OPENROUTER_SITE_URL: str = ""

    DEFAULT_LLM_PROVIDER: str = "ollama"

    # Mem0 Memory Configuration
    MEM0_LLM_PROVIDER: str = "ollama"  # "ollama" or "openrouter"
    MEM0_MODEL: str = "granite4:micro"  # Model for memory extraction
    MEM0_ENABLE_MEMORY: bool = True  # Enable/disable memory system

    # TTS Configuration
    TTS_ENABLED: bool = True  # Enable/disable TTS
    TTS_PROVIDER: str = "piper"
    PIPER_TTS_URL: str = "http://piper:10200"  # Piper TTS service URL
    PIPER_DEFAULT_VOICE: str = "en_US-lessac-medium"
    AUDIO_CACHE_PATH: str = "/app/audio_cache"

    # STT Configuration
    STT_ENABLED: bool = True  # Enable/disable STT
    STT_PROVIDER: str = "whisper"
    WHISPER_STT_URL: str = "http://whisper:10300"  # Whisper STT service URL
    WHISPER_MODEL: str = "base-int8"  # Whisper model (tiny, base, small, medium, large-v3)
    WHISPER_LANGUAGE: str = "en"  # Language code for transcription

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
