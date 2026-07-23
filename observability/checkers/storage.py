import time
from pathlib import Path
from observability.checkers.base import BaseHealthChecker, HealthResult


class StorageChecker(BaseHealthChecker):
    """Health checker testing local and object storage path accessibility."""

    @property
    def name(self) -> str:
        return "storage"

    async def check(self) -> HealthResult:
        start = time.perf_counter()
        try:
            storage_path = Path(__file__).parent.parent.parent / "storage"
            writable = storage_path.exists()
            latency_ms = (time.perf_counter() - start) * 1000.0
            return HealthResult(
                name=self.name,
                healthy=writable,
                status="healthy" if writable else "unhealthy",
                latency_ms=round(latency_ms, 2),
                details={"storage_path": str(storage_path)},
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
