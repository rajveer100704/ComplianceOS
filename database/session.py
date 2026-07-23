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
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import create_async_engine
    from database.engine import _set_sqlite_pragmas

    engine = create_async_engine(
        "sqlite+aiosqlite:///compliance.db?timeout=60",
        echo=False,
        connect_args={"timeout": 60},
    )
    event.listen(engine.sync_engine, "connect", _set_sqlite_pragmas)
    async_session_factory.configure(bind=engine)
