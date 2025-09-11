from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config.settings import SETTINGS


@asynccontextmanager
async def get_checkpointer():
    """Get a Postgres checkpointer instance."""
    async with AsyncPostgresSaver.from_conn_string(
        SETTINGS.database_url
    ) as checkpointer:
        yield checkpointer
