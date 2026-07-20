from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import async_session_factory

@asynccontextmanager
async def transaction_scope() -> AsyncGenerator[AsyncSession, None]:
    """Context manager executing block operations inside auto-committing/auto-rolling back transaction."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
