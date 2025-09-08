"""Database configuration and session management."""

from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings
from app.core.exceptions import DatabaseError


@lru_cache
def get_async_engine():
    """Get cached async SQLAlchemy engine."""
    settings = get_settings()
    if not settings.database_url:
        raise DatabaseError("Database connection not configured")

    # Convert psycopg connection string to async
    async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

    return create_async_engine(
        async_url,
        echo=settings.debug,
        future=True,
        pool_pre_ping=True,
    )


@lru_cache
def get_async_session_maker():
    """Get cached async session maker."""
    engine = get_async_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
