"""Content moderation service with caching."""

import hashlib
from functools import lru_cache
from typing import Optional

from openai import AsyncOpenAI

from app.config.settings import get_settings


class ModeratorService:
    """Fast content moderation with caching."""

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not self.settings.openai_api_key:
                raise ValueError("OpenAI API key is required for moderation")
            self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self._client

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
