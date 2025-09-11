
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App settings
    app_name: str = Field(default="WeAssistant", alias="APP_NAME")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")

    # Database settings
    database_url: str = Field(..., alias="DATABASE_URL")
    database_schema: str = Field(default="public", alias="DATABASE_SCHEMA")
    database_pool_min_size: int = Field(default=5, alias="DATABASE_POOL_MIN_SIZE")
    database_pool_max_size: int = Field(default=20, alias="DATABASE_POOL_MAX_SIZE")

    # OpenAI settings
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-5-nano", alias="OPENAI_CHAT_MODEL")
    openai_embed_model: str = Field(
        default="text-embedding-3-large", alias="OPENAI_EMBED_MODEL"
    )
    openai_max_context_length: int = Field(
        default=5000, alias="OPENAI_MAX_CONTEXT_LENGTH"
    )

    # RAG settings
    rag_chunk_size: int = Field(default=800, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=100, alias="RAG_CHUNK_OVERLAP")
    rag_top_k: int = Field(default=3, alias="RAG_TOP_K")
    rag_score_threshold: float = Field(default=0.7, alias="RAG_SCORE_THRESHOLD")

    # Cache settings
    cache_ttl_minutes: int = Field(default=10, alias="CACHE_TTL_MINUTES")
    cache_max_count: int = Field(default=100, alias="CACHE_MAX_COUNT")


def setup_settings() -> Settings:
    """Get cached settings instance."""
    global SETTINGS
    SETTINGS = Settings()  # type: ignore
    return SETTINGS


SETTINGS = None
setup_settings()