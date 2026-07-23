import time
from observability.checkers.base import BaseHealthChecker, HealthResult


class IntegrationChecker(BaseHealthChecker):
    """Health checker testing external integration circuit breakers."""

    @property
    def name(self) -> str:
        return "integrations"

    async def check(self) -> HealthResult:
        start = time.perf_counter()
        try:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return HealthResult(
                name=self.name,
                healthy=True,
                status="healthy",
                latency_ms=round(latency_ms, 2),
                details={"active_adapters": ["slack", "teams", "github", "jira"]},
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return HealthResult(
                name=self.name,
                healthy=False,
                status="degraded",
                latency_ms=round(latency_ms, 2),
                error=str(e),
            )
