import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from retrieval.config.loader import ConfigLoader


def get_database_url() -> str:
    """Returns connection URL, preferring DATABASE_URL env var over app.yaml configuration."""
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    config = ConfigLoader.load()
    db_config = config.get("database", {})
    provider = db_config.get("provider", "sqlite")

    if provider == "sqlite":
        return "sqlite+aiosqlite:///compliance.db?timeout=30"
    return db_config.get(
        "url", "postgresql+asyncpg://postgres:postgres@localhost:5432/compliance_os"
    )


def create_db_engine() -> AsyncEngine:
    """Constructs AsyncEngine based on profile parameters."""
    url = get_database_url()
    config = ConfigLoader.load()
    db_config = config.get("database", {})

    kwargs = {}
    if "sqlite" in url:
        kwargs["connect_args"] = {"timeout": 60}
    elif "postgresql" in url or db_config.get("provider") == "postgresql":
        kwargs["pool_size"] = db_config.get("pool_size", 10)
        kwargs["max_overflow"] = db_config.get("max_overflow", 5)
        kwargs["pool_timeout"] = db_config.get("timeout", 30)
        kwargs["pool_recycle"] = 1800

    return create_async_engine(url, echo=db_config.get("echo", False), **kwargs)
