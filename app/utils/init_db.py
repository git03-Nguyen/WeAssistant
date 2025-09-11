"""Database initialization and migration utilities."""

from langchain_postgres.v2.engine import PGEngine
from sqlalchemy import text

from app.config.settings import SETTINGS, setup_settings
from app.core.checkpoint import get_checkpointer
from app.models.base import Base
from app.utils.database import (
    close_db_connections,
    get_async_engine,
    open_db_connections,
)

setup_settings()

async def acreate_tables():
    """Create all database tables."""
    print("Creating database tables...")
    try:
        await open_db_connections()
        engine = get_async_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {SETTINGS.database_schema};")
            )
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()

        async with get_checkpointer() as checkpointer:
            await checkpointer.setup()
        await PGEngine.from_engine(engine).ainit_vectorstore_table(
            table_name="embeddings",
            vector_size=3072,
            schema_name=SETTINGS.database_schema,
        )
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
    finally:
        await close_db_connections()


async def adrop_tables():
    """Drop all database tables."""
    print("Dropping database tables...")
    try:
        await open_db_connections()
        engine = get_async_engine()

        async with engine.begin() as conn:
            await conn.execute(
                text(f"DROP SCHEMA IF EXISTS {SETTINGS.database_schema} CASCADE;")
            )
            await conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {SETTINGS.database_schema};")
            )
            await conn.commit()
        print("✅ Database tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping database tables: {e}")
    finally:
        await close_db_connections()
