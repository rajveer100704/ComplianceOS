import logging
from sqlalchemy import text
from database.session import async_session_factory, fallback_to_sqlite
from database.retry import retry_async
from retrieval.config.loader import ConfigLoader

logger = logging.getLogger("database_bootstrap")


async def bootstrap_database() -> None:
    """Verifies connection health and enables required PostgreSQL extensions like pgvector."""
    config = ConfigLoader.load()
    db_config = config.get("database", {})
    allow_fallback = db_config.get("allow_sqlite_fallback", True)

    async def _check_and_bootstrap():
        async with async_session_factory() as session:
            conn = await session.connection()
            dialect_name = conn.dialect.name

            if dialect_name == "postgresql":
                # Ensure pgvector extension is enabled
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                await session.commit()
            else:
                # SQLite simple connection test query
                await session.execute(text("SELECT 1;"))

    try:
        # Reduced retries for fallback scenario to avoid long startup delays
        await retry_async(_check_and_bootstrap, retries=2, backoff_seconds=0.2)
    except Exception as e:
        if allow_fallback:
            fallback_to_sqlite()
            # Verify SQLite fallback connection works
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1;"))
        else:
            raise e
