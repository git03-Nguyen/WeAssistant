"""Thread service for thread-related operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.thread import Thread


class ThreadService:
    """Simplified service for thread operations - only needed methods."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def acreate_thread(self, user_id: str) -> Thread:
        """Create a new thread."""
        try:
            thread = Thread(user_id=user_id)
            self.session.add(thread)
            await self.session.commit()
            return thread
        except Exception as e:
            raise DatabaseError(f"Failed to create thread: {e}")

    async def aget_thread(self, thread_id: str) -> Optional[Thread]:
        """Get thread by ID."""
        try:
            stmt = (
                select(Thread)
                .where(Thread.id == thread_id)
                .where(Thread.deleted_at.is_(None))
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Failed to get thread: {e}")

    async def aget_threads(self, user_id: str | None = None) -> list[Thread]:
        """List threads"""
        query = (
            select(Thread)
            .where(Thread.deleted_at.is_(None))
            .order_by(Thread.created_at.desc())
        )
        if user_id:
            query = query.where(Thread.user_id == user_id)

        result = await self.session.execute(query)
        threads = result.scalars().all()

        return list(threads)
