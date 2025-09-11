"""Dependency injection for API endpoints."""

from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.services.chat_service import ChatService
from app.services.documents import DocumentService
from app.services.threads import ThreadService
from app.utils.database import get_asyncpg_sessionmaker, get_psycopg_pool


@asynccontextmanager
async def aget_asyncpg_session():
    """AsyncSession backed by asyncpg engine."""
    async with get_asyncpg_sessionmaker().begin() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def aget_psycopg_conn():
    """Get a connection from the psycopg pool."""
    async with get_psycopg_pool().connection() as conn:
        try:
            yield conn
        except Exception:
            await conn.rollback()
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

def get_chat_service(
    session: AsyncSession = Depends(aget_asyncpg_session),
) -> ChatService:
    """Get chat service instance."""
    return ChatService(session)