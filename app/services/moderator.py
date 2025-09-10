"""Content moderation service with caching and connection pooling."""

import hashlib
from functools import lru_cache
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config.settings import get_settings

# Global connection pool for OpenAI client
_openai_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """Get or create a shared OpenAI client with connection pooling."""
    global _openai_client
    if _openai_client is None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for moderation")

        # Create HTTP client with connection pooling
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=10, max_connections=20, keepalive_expiry=30.0
            ),
            timeout=30.0,
        )

        _openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key, http_client=http_client
        )
    return _openai_client


class ModeratorService:
    """Fast content moderation with caching and pooled connections."""

    def __init__(self):
        pass  # No need to store settings or client

    @property
    def client(self) -> AsyncOpenAI:
        """Get shared OpenAI client with connection pooling."""
        return get_openai_client()

    @lru_cache(maxsize=1000)
    def _get_content_hash(self, content: str) -> str:
        """Generate hash for content caching."""
        return hashlib.md5(content.encode()).hexdigest()

    # Cache for moderation results (in production, consider Redis)
    _moderation_cache: dict[str, bool] = {}

    async def is_content_safe(self, content: str) -> bool:
        """Check if content is safe with caching."""
        if not content.strip():
            return True

        # Check cache first
        content_hash = self._get_content_hash(content)
        if content_hash in self._moderation_cache:
            return self._moderation_cache[content_hash]

        try:
            response = await self.client.moderations.create(input=content)
            is_safe = not response.results[0].flagged

            # Cache the result
            self._moderation_cache[content_hash] = is_safe
            return is_safe

        except Exception:
            # Fail-open for availability
            return True

    @classmethod
    def clear_cache(cls):
        """Clear moderation cache."""
        cls._moderation_cache.clear()


async def close_openai_client():
    """Close the shared OpenAI client and its connection pool."""
    global _openai_client
    if _openai_client is not None:
        if hasattr(_openai_client, "_client") and _openai_client._client:
            await _openai_client._client.aclose()
        _openai_client = None
