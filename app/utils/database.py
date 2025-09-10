"""Database configuration and session management."""

import asyncio
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator, Optional

from psycopg_pool import AsyncConnectionPool
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


# PostgreSQL connection pool for chat history
_postgres_pool: Optional[AsyncConnectionPool] = None


async def get_postgres_pool() -> AsyncConnectionPool:
    """Get or create the PostgreSQL connection pool."""
    global _postgres_pool

    if _postgres_pool is None:
        settings = get_settings()
        if not settings.database_url:
            raise DatabaseError("Database URL not configured")

        _postgres_pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            open=False,  # Don't open immediately
        )
        await _postgres_pool.open()

    return _postgres_pool


@asynccontextmanager
async def get_postgres_connection():
    """Get a connection from the pool."""
    pool = await get_postgres_pool()
    async with pool.connection() as conn:
        yield conn


async def close_postgres_pool():
    """Close the PostgreSQL connection pool."""
    global _postgres_pool
    if _postgres_pool is not None:
        await _postgres_pool.close()
        _postgres_pool = None


async def cleanup_all_connections():
    """Close all connection pools (PostgreSQL and OpenAI)."""
    # Close PostgreSQL pool
    await close_postgres_pool()

    # Close OpenAI client pool
    try:
        from app.services.moderator import close_openai_client

        await close_openai_client()
    except ImportError:
        pass  # OpenAI client not available


async def ensure_chat_history_tables(table_name: str = "history") -> bool:
    """Ensure chat history tables exist."""
    try:
        from langchain_postgres import PostgresChatMessageHistory

        async with get_postgres_connection() as connection:
            await PostgresChatMessageHistory.acreate_tables(connection, table_name)
        return True
    except Exception as e:
        print(f"Warning: Failed to ensure chat history tables: {e}")
        return False


def clear_postgres_connection_cache():
    """Clear the cached PostgreSQL connection and close all pools."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule the cleanup to run later if we're in an async context
            asyncio.create_task(cleanup_all_connections())
        else:
            # Run the cleanup if we're not in an async context
            asyncio.run(cleanup_all_connections())
    except Exception:
        pass  # Best effort cleanup
