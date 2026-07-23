import time
import httpx
from config.settings import settings
from observability.checkers.base import BaseHealthChecker, HealthResult


class QdrantChecker(BaseHealthChecker):
    """Health checker testing Qdrant vector database HTTP ping."""

    @property
    def name(self) -> str:
        return "qdrant"

    async def check(self) -> HealthResult:
        start = time.perf_counter()
        try:
            url = f"{settings.QDRANT_URL.rstrip('/')}/collections"
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                res.raise_for_status()
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
                status="degraded",
                latency_ms=round(latency_ms, 2),
                error=f"Qdrant unreachable: {e}",
            )
