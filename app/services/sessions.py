"""Session and chat history management with PostgreSQL backend."""

import asyncio
from typing import Dict, List, Optional

from langchain_core.messages import BaseMessage
from langchain_postgres import PostgresChatMessageHistory
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import (
    get_postgres_connection,
)


class SessionManager:
    """Async PostgreSQL-based session and history management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._session_cache: Dict[str, PostgresChatMessageHistory] = {}
        self._async_connection = None
        self._table_name = "history"

    async def _get_connection(self):
        """Get async PostgreSQL connection."""
        if self._async_connection is None:
            self._async_connection = await get_postgres_connection()
        return self._async_connection

    async def _create_history(self, session_id: str) -> PostgresChatMessageHistory:
        """Create PostgresChatMessageHistory instance."""
        connection = await self._get_connection()
        return PostgresChatMessageHistory(
            self._table_name, session_id, async_connection=connection
        )

    async def get_session_history(self, session_id: str) -> PostgresChatMessageHistory:
        """Get session history."""
        if session_id not in self._session_cache:
            history = await self._create_history(session_id)
            self._session_cache[session_id] = history
        return self._session_cache[session_id]

    async def add_messages(self, session_id: str, messages: List[BaseMessage]):
        """Add messages to history."""
        history = await self.get_session_history(session_id)
        await history.aadd_messages(messages)

    async def get_thread_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[BaseMessage]:
        """Get thread messages from PostgresChatMessageHistory."""
        history = await self.get_session_history(session_id)
        messages = await history.aget_messages()

        if limit:
            messages = messages[-limit:]

        return messages

    async def clear_cache(self, session_id: str):
        """Clear session from cache only (does not delete database data)."""
        if session_id in self._session_cache:
            del self._session_cache[session_id]

    def get_session_history_sync(self, session_id: str) -> PostgresChatMessageHistory:
        """Sync wrapper for LangChain compatibility."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_session_history(session_id))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.get_session_history(session_id))
