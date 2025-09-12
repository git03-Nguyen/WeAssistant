"""Dependency injection for API endpoints."""

from fastapi import Depends
from psycopg import AsyncConnection
from psycopg.rows import DictRow
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.agent import AgentService
from app.services.documents import DocumentService
from app.services.threads import ThreadService
from app.services.users import UserService
from app.utils.database import get_asyncpg_engine, get_psycopg_pool


async def aget_asyncpg_session():
    """AsyncSession backed by asyncpg engine."""
    maker = async_sessionmaker(
        bind=get_asyncpg_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def aget_psycopg_conn(*, autocommit: bool = False):
    """Get a connection from the psycopg pool."""
    async with get_psycopg_pool().connection() as conn:
        bak_autocommit = conn.autocommit
        try:
            await conn.set_autocommit(autocommit)
            yield conn
        except Exception:
            await conn.rollback()
            raise
        finally:
            if autocommit != bak_autocommit:
                await conn.set_autocommit(bak_autocommit)


def get_user_service(
    session: AsyncSession = Depends(aget_asyncpg_session),
) -> UserService:
    """Get user service instance."""
    return UserService(session)


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


def get_agent_service(
    conn: AsyncConnection[DictRow] = Depends(aget_psycopg_conn),
) -> AgentService:
    """Get chat service instance."""
    return AgentService(conn)