"""Dependency injection for API endpoints."""

from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.services.agent import AgentService
from app.services.documents import DocumentService
from app.services.threads import ThreadService
from app.utils.database import get_asyncpg_sessionmaker


@asynccontextmanager
async def aget_asyncpg_session():
    """AsyncSession backed by asyncpg engine."""
    async with get_asyncpg_sessionmaker().begin() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_document_service(
    session: AsyncSession = Depends(aget_asyncpg_session),
) -> DocumentService:
    """Get document service instance."""
    return DocumentService(session)


def get_thread_service(
    session: AsyncSession = Depends(aget_asyncpg_session),
) -> ThreadService:
    """Get thread service instance."""
    return ThreadService(session)

def get_agent_service() -> AgentService:
    """Get chat service instance."""
    return AgentService()