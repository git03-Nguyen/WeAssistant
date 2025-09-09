"""Database initialization and migration utilities."""

from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.base import Base
from app.utils.database import ensure_chat_history_tables, get_async_engine


async def create_tables():
    """Create all database tables."""
    engine: AsyncEngine = get_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created successfully")


async def create_chat_history_tables():
    """Create PostgreSQL chat message history tables."""
    try:
        success = await ensure_chat_history_tables("history")
        if success:
            print("✅ Chat message history tables created successfully")
        else:
            print("⚠️ Failed to create chat history tables")
    except Exception as e:
        print(f"⚠️ Failed to create chat history tables: {e}")


async def initialize_database():
    """Initialize all database tables and migrations."""
    print("🚀 Initializing database...")

    # Create main application tables
    await create_tables()

    # Create chat message history tables
    await create_chat_history_tables()

    print("✅ Database initialization completed")


async def drop_tables():
    """Drop all database tables."""
    engine: AsyncEngine = get_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await drop_chat_history_tables()

    print("✅ Database tables dropped successfully")


async def drop_chat_history_tables():
    """Drop PostgreSQL chat message history tables."""
    try:
        from langchain_postgres import PostgresChatMessageHistory

        from app.utils.database import get_postgres_connection

        connection = await get_postgres_connection()
        await PostgresChatMessageHistory.adrop_table(connection, "history")
        print("✅ Chat message history tables dropped successfully")

    except Exception as e:
        print(f"⚠️ Failed to drop chat history tables: {e}")


if __name__ == "__main__":
    import asyncio

    print("Initializing database...")
    asyncio.run(initialize_database())
