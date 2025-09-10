"""Session and chat history management with PostgreSQL backend."""

from typing import List, Optional

from langchain_core.messages import BaseMessage
from langchain_postgres import PostgresChatMessageHistory
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import get_postgres_connection


class HistoryManager:
    """Async PostgreSQL-based session and history management with connection pooling."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._table_name = "history"

    async def get_history_manager(
        self, session_id: str, connection
    ) -> PostgresChatMessageHistory:
        """Create PostgresChatMessageHistory instance with pooled connection."""
        return PostgresChatMessageHistory(
            self._table_name, session_id, async_connection=connection
        )

    async def get_session_history(self, session_id: str) -> PostgresChatMessageHistory:
        """Get session history using a pooled connection."""
        # Note: This returns a history object that will need to be used within a connection context
        # For most use cases, prefer the specific methods below that handle the connection automatically
        async with get_postgres_connection() as connection:
            return await self.get_history_manager(session_id, connection)

    async def add_messages(self, session_id: str, messages: List[BaseMessage]):
        """Add messages to history using a pooled connection."""
        async with get_postgres_connection() as connection:
            history = await self.get_history_manager(session_id, connection)
            await history.aadd_messages(messages)

    async def get_thread_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[BaseMessage]:
        """Get thread messages from PostgresChatMessageHistory using a pooled connection."""
        async with get_postgres_connection() as connection:
            history = await self.get_history_manager(session_id, connection)
            messages = await history.aget_messages()

            if limit:
                messages = messages[-limit:]

            return messages

    def get_session_history_sync(self, session_id: str) -> PostgresChatMessageHistory:
        """Sync wrapper for LangChain compatibility."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_session_history(session_id))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.get_session_history(session_id))
