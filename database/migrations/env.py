import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from database.engine import get_database_url

# import Base and models for metadata resolution
from database.models.base import Base
from database.models.request import RequestModel
from database.models.document import DocumentModel
from database.models.run import RunModel
from database.models.claim import ClaimModel
from database.models.audit import AuditLogModel
from database.models.requirement import RequirementModel
from database.models.outbox import OutboxEventModel
from database.models.chunk import ChunkModel
from database.models.task import TaskModel
from database.models.review import (
    ReviewAssignmentModel,
    ReviewActivityLogModel,
    CommentMentionModel,
    ClaimCommentModel,
    PinnedEvidenceModel,
    ReviewSnapshotModel,
)
from database.models.report import (
    ReportTemplateModel,
    ReportModel,
    ReportSectionModel,
    ReportFindingModel,
    ReportCitationModel,
    ReportActivityLogModel,
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine and associate a connection."""
    url = get_database_url()
    from retrieval.config.loader import ConfigLoader
    config_yaml = ConfigLoader.load()
    db_config = config_yaml.get("database", {})
    allow_fallback = db_config.get("allow_sqlite_fallback", True)

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    try:
        connectable = async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()
    except Exception as e:
        if allow_fallback:
            print("PostgreSQL connection refused in Alembic. Falling back to local SQLite migration...")
            configuration["sqlalchemy.url"] = "sqlite+aiosqlite:///compliance.db"
            connectable = async_engine_from_config(
                configuration,
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )
            async with connectable.connect() as connection:
                await connection.run_sync(do_run_migrations)
            await connectable.dispose()
        else:
            raise e

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    def _run():
        asyncio.run(run_async_migrations())
    try:
        asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run)
            future.result()
    except RuntimeError:
        asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
