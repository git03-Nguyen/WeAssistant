"""
Centralised DB helpers for BOTH drivers: psycopg 3 and asyncpg (SQLAlchemy).
"""

from contextlib import asynccontextmanager
from functools import lru_cache

from psycopg import AsyncConnection
from psycopg.rows import DictRow
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import SETTINGS


# ---------------------------------------------------------------------------
# PSYCOPG 3
# ---------------------------------------------------------------------------
@lru_cache
def get_psycopg_pool() -> AsyncConnectionPool[AsyncConnection[DictRow]]:
    """Get or create the global psycopg connection pool."""
    return AsyncConnectionPool(
        conninfo=SETTINGS.database_url,
        min_size=SETTINGS.database_pool_min_size,
        max_size=SETTINGS.database_pool_max_size,
        open=False,
    )


@asynccontextmanager
async def aget_psycopg_conn(*, autocommit: bool = False):
    """Get a connection from the psycopg pool."""
    conn = await get_psycopg_pool().getconn()
    bak_autocommit = conn.autocommit
    try:
        await conn.set_autocommit(autocommit)
        yield conn
    finally:
        await conn.set_autocommit(bak_autocommit)
        await get_psycopg_pool().putconn(conn)


# ---------------------------------------------------------------------------
# ASYNCPG (default SQLAlchemy ORM)
# ---------------------------------------------------------------------------
@lru_cache
def get_async_engine():
    """Get or create the global asyncpg engine for SQLAlchemy."""
    return create_async_engine(
        url=SETTINGS.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=SETTINGS.database_pool_min_size,
        max_overflow=SETTINGS.database_pool_max_size - SETTINGS.database_pool_min_size,
        echo=SETTINGS.app_debug,
    )

@lru_cache
def get_asyncpg_sessionmaker():
    """Get or create the global asyncpg sessionmaker for SQLAlchemy."""
    return async_sessionmaker(
        bind=get_async_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


# ---------------------------------------------------------------------------
# Startup / Shutdown helpers
# ---------------------------------------------------------------------------
async def open_db_connections() -> None:
    """Open the psycopg connection pool."""
    await get_psycopg_pool().open()


async def close_db_connections() -> None:
    """Close the psycopg connection pool and dispose the asyncpg engine."""
    await get_psycopg_pool().close()
    await get_async_engine().dispose()
