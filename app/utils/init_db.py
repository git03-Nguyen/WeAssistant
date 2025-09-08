"""Database initialization and migration utilities."""

from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.base import Base
from app.utils.database import get_async_engine


async def create_tables():
    """Create all database tables."""
    engine: AsyncEngine = get_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created successfully")


async def drop_tables():
    """Drop all database tables."""
    engine: AsyncEngine = get_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("✅ Database tables dropped successfully")


if __name__ == "__main__":
    import asyncio

    print("Creating database tables...")
    asyncio.run(create_tables())
