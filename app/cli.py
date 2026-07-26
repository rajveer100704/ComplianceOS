"""CLI entry points for database migrations, seeding, indexing, and server startup."""

import asyncio
import logging
import typer
import uvicorn
from database.engine import init_db

cli = typer.Typer(help="ComplianceOS CLI Management Utility")
logger = logging.getLogger("complianceos.cli")


@cli.command()
def migrate():
    """Run database initialization and Alembic schema migrations."""
    logger.info("Executing database schema migrations...")
    asyncio.run(init_db())
    typer.echo("Database migrations completed successfully.")


@cli.command()
def seed():
    """Seed initial engineering standards and regulatory data."""
    logger.info("Seeding initial regulatory data...")
    from main import seed_requirements

    asyncio.run(seed_requirements())
    typer.echo("Regulatory dataset seeding completed.")


@cli.command()
def run(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run production ASGI server."""
    logger.info(f"Starting ComplianceOS server on {host}:{port}...")
    uvicorn.run("main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    cli()
