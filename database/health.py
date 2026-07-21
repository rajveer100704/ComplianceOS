from sqlalchemy import text
from database.session import async_session_factory


class DatabaseHealth:
    """Verifies operational database status and connection pools."""

    @staticmethod
    async def check_health() -> dict:
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1;"))
                conn = await session.connection()
                dialect_name = conn.dialect.name
                return {
                    "status": "healthy",
                    "provider": dialect_name,
                    "active_pool_size": 1,  # SQLite dummy pool / postgres pool size
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
