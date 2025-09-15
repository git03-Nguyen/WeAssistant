"""Message service for message-related operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.message import Message


class MessageService:
    """Simplified service for message operations - only needed methods."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def acreate_message(
        self,
        user_id: str,
        thread_id: str,
        type: str,
        content: str,
    ) -> Message:
        """Create a new message."""
        try:
            message = Message(
                content=content,
                type=type,
            )
            self.session.add(message)
            await self.session.flush()
            return message
        except Exception as e:
            raise DatabaseError(f"Failed to create message: {e}")

    async def aget_messages(self, thread_id: str) -> list[Message]:
        """Get messages history for a thread."""
        try:
            stmt = (
                select(Message)
                .where(Message.thread_id == thread_id)
                .where(Message.deleted_at.is_(None))
            )

            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            return list(messages)

        except Exception as e:
            raise DatabaseError(f"Failed to get messages: {e}")
