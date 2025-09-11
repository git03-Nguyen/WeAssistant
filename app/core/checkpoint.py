from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow


def get_checkpointer(conn: AsyncConnection[DictRow]) -> AsyncPostgresSaver:
    """Get a Postgres checkpointer instance."""
    return AsyncPostgresSaver(conn)
