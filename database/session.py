import logging
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from database.engine import create_db_engine

logger = logging.getLogger("database_session")

engine = create_db_engine()
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def fallback_to_sqlite():
    """Switches the session factory binding to a local SQLite fallback database."""
    global engine, async_session_factory
    logger.warning(
        "PostgreSQL connection refused. Falling back to local SQLite database..."
    )
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        "sqlite+aiosqlite:///compliance.db?timeout=30", echo=False
    )
    async_session_factory.configure(bind=engine)
