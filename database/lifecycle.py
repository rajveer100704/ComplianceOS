from database.session import engine
from database.bootstrap import bootstrap_database

async def db_startup_warmup() -> None:
    """Invoked during FastAPI startup lifecycle to verify database connection health."""
    await bootstrap_database()

async def db_shutdown_teardown() -> None:
    """Disposes engine connection pool cleanly on application shutdown."""
    await engine.dispose()
