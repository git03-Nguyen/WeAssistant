"""Session and chat history management with caching."""

import asyncio
from functools import lru_cache
from typing import Dict, List, Optional

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class SessionManager:
    """Efficient session and history management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._session_cache: Dict[str, BaseChatMessageHistory] = {}

    @lru_cache(maxsize=100)
    def _create_empty_history(self) -> ChatMessageHistory:
        """Create cached empty history instance."""
        return ChatMessageHistory()

    def get_session_history_sync(self, thread_id: str) -> BaseChatMessageHistory:
        """Get session history synchronously for LangChain compatibility."""
        if thread_id not in self._session_cache:
            # Run the async method in the current event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, return empty history and load async
                    # This is a compromise for LangChain's sync interface
                    history = ChatMessageHistory()
                    self._session_cache[thread_id] = history
                    # Schedule async loading
                    asyncio.create_task(self._load_and_update_history(thread_id))
                    return history
                else:
                    self._session_cache[thread_id] = loop.run_until_complete(
                        self._load_thread_history(thread_id)
                    )
            except RuntimeError:
                # No event loop, return empty history
                self._session_cache[thread_id] = ChatMessageHistory()

        return self._session_cache[thread_id]

    async def get_session_history(self, thread_id: str) -> BaseChatMessageHistory:
        """Get session history with caching."""
        if thread_id not in self._session_cache:
            self._session_cache[thread_id] = await self._load_thread_history(thread_id)
        return self._session_cache[thread_id]

    async def _load_and_update_history(self, thread_id: str):
        """Load history async and update cache."""
        try:
            history = await self._load_thread_history(thread_id)
            self._session_cache[thread_id] = history
        except Exception as e:
            print(f"Warning: Failed to load async history for {thread_id}: {e}")

    async def _load_thread_history(self, thread_id: str) -> BaseChatMessageHistory:
        """Load chat history from database."""
        chat_history = ChatMessageHistory()

        try:
            stmt = (
                select(Message)
                .where(Message.thread_id == thread_id)
                .where(Message.deleted_at.is_(None))
                .order_by(Message.created_at.asc())
                .limit(20)  # Limit for performance
            )

            result = await self.session.execute(stmt)
            messages = result.scalars().all()

            for message in messages:
                if message.role == "user":
                    chat_history.add_user_message(message.content)
                elif message.role == "assistant":
                    chat_history.add_ai_message(message.content)

        except Exception as e:
            print(f"Warning: Failed to load session history: {e}")

        return chat_history

    async def get_thread_messages(
        self, thread_id: str, limit: Optional[int] = None
    ) -> List[Message]:
        """Get thread messages for API responses."""
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.asc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def invalidate_cache(self, thread_id: str):
        """Invalidate cached session history."""
        if thread_id in self._session_cache:
            del self._session_cache[thread_id]

    def clear_all_cache(self):
        """Clear all cached sessions."""
        self._session_cache.clear()
        self._create_empty_history.cache_clear()
