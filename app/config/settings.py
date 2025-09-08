from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # App settings
    app_name: str = Field(default="WeAssistant", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    version: str = Field(default="0.1.0", alias="VERSION")

    # Database settings
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-5-nano", alias="OPENAI_CHAT_MODEL")
    openai_classifier_model: str = Field(
        default="gpt-5-nano", alias="OPENAI_CLASSIFIER_MODEL"
    )
    openai_embed_model: str = Field(
        default="text-embedding-3-large", alias="OPENAI_EMBED_MODEL"
    )

    # Qdrant settings
    qdrant_url: Optional[str] = Field(default=None, alias="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(
        default="wemastertrade_kb", alias="QDRANT_COLLECTION"
    )

    # Chat settings
    retrieval_k: int = Field(default=6, alias="RETRIEVAL_K")
    confidence_threshold: float = Field(default=0.6, alias="CONFIDENCE_THRESHOLD")
    high_confidence_threshold: float = Field(
        default=0.7, alias="HIGH_CONFIDENCE_THRESHOLD"
    )

    # RAG settings
    relevance_threshold: float = Field(default=0.7, alias="RELEVANCE_THRESHOLD")
    min_context_length: int = Field(default=50, alias="MIN_CONTEXT_LENGTH")

    # Cost optimization settings
    max_context_length: int = Field(default=1500, alias="MAX_CONTEXT_LENGTH")
    cache_ttl_minutes: int = Field(default=10, alias="CACHE_TTL_MINUTES")
    max_cache_size: int = Field(default=100, alias="MAX_CACHE_SIZE")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
