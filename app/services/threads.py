"""Thread service for thread-related operations."""

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.thread import Thread
from app.schemas.thread import ThreadCreateRequest


class ThreadService:
    """Simplified service for thread operations - only needed methods."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_thread(self, request: ThreadCreateRequest) -> Thread:
        """Create a new thread."""
        try:
            thread = Thread(user_id=request.user_id)
            self.session.add(thread)
            await self.session.flush()
            return thread
        except Exception as e:
            raise DatabaseError(f"Failed to create thread: {e}")

    async def get_thread(self, thread_id: str) -> Optional[Thread]:
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

    async def list_threads(
        self, user_id: Optional[str] = None, page: int = 1, size: int = 10
    ) -> Tuple[List[Thread], int]:
        """List threads with pagination and optional filtering."""
        try:
            # Build base query
            query = select(Thread).where(Thread.deleted_at.is_(None))

            # Apply user filter if provided
            if user_id:
                query = query.where(Thread.user_id == user_id)

            # Get total count
            count_query = select(func.count(Thread.id)).where(
                Thread.deleted_at.is_(None)
            )
            if user_id:
                count_query = count_query.where(Thread.user_id == user_id)

            total_result = await self.session.execute(count_query)
            total = total_result.scalar()

            # Apply pagination
            offset = (page - 1) * size
            query = query.offset(offset).limit(size).order_by(Thread.created_at.desc())

            result = await self.session.execute(query)
            threads = result.scalars().all()

            return list(threads), total or 0
        except Exception as e:
            raise DatabaseError(f"Failed to list threads: {e}")
