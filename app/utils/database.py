"""Database configuration and session management."""

from functools import lru_cache
from typing import AsyncGenerator

import psycopg
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


# PostgreSQL connection utilities for chat history
@lru_cache(maxsize=1)
async def get_postgres_connection() -> psycopg.AsyncConnection:
    """Get async PostgreSQL connection for chat history."""
    settings = get_settings()
    conn_string = settings.database_url

    if not conn_string:
        raise ValueError("Database URL not configured")

    return await psycopg.AsyncConnection.connect(conn_string)


async def ensure_chat_history_tables(table_name: str = "history") -> bool:
    """Ensure chat history tables exist."""
    try:
        from langchain_postgres import PostgresChatMessageHistory

        connection = await get_postgres_connection()
        await PostgresChatMessageHistory.acreate_tables(connection, table_name)
        return True
    except Exception as e:
        print(f"Warning: Failed to ensure chat history tables: {e}")
        return False


def clear_postgres_connection_cache():
    """Clear the cached PostgreSQL connection."""
    get_postgres_connection.cache_clear()
