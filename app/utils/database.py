"""
Centralised DB helpers for BOTH drivers: psycopg 3 and asyncpg (SQLAlchemy).
"""

from functools import lru_cache

from psycopg import AsyncConnection
from psycopg.rows import DictRow
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import (
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


# ---------------------------------------------------------------------------
# ASYNCPG (default SQLAlchemy ORM)
# ---------------------------------------------------------------------------
@lru_cache
def get_asyncpg_engine():
    """Get or create the global asyncpg engine for SQLAlchemy."""
    return create_async_engine(
        url=SETTINGS.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=SETTINGS.database_pool_min_size,
        max_overflow=SETTINGS.database_pool_max_size - SETTINGS.database_pool_min_size,
        echo=SETTINGS.app_debug,
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
    await get_asyncpg_engine().dispose()
