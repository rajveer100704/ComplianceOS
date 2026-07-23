import time
from sqlalchemy import text
from database.session import async_session_factory
from observability.checkers.base import BaseHealthChecker, HealthResult


class DatabaseChecker(BaseHealthChecker):
    """Health checker testing SQLAlchemy async database connection pool."""

    @property
    def name(self) -> str:
        return "database"

    async def check(self) -> HealthResult:
        start = time.perf_counter()
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start) * 1000.0
            return HealthResult(
                name=self.name,
                healthy=True,
                status="healthy",
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return HealthResult(
                name=self.name,
                healthy=False,
                status="unhealthy",
                latency_ms=round(latency_ms, 2),
                error=str(e),
            )
