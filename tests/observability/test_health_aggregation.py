import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from observability.health import HealthService
from observability.checkers.base import BaseHealthChecker, HealthResult


class DummySuccessChecker(BaseHealthChecker):
    @property
    def name(self) -> str:
        return "dummy_db"

    async def check(self) -> HealthResult:
        return HealthResult("dummy_db", True, "healthy", 1.2)


@pytest.mark.asyncio
async def test_health_service_aggregation():
    """Test HealthService aggregates checker results correctly."""
    service = HealthService(checkers=[DummySuccessChecker()])
    report = await service.run_checkers()
    assert "dummy_db" in report
    assert report["dummy_db"].healthy is True


@pytest.mark.asyncio
async def test_liveness_and_readiness_endpoints():
    """Test /healthz and /readyz HTTP endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        res_liveness = await client.get("/healthz")
        assert res_liveness.status_code == 200
        assert res_liveness.json()["status"] == "ok"

        res_ready = await client.get("/readyz")
        assert res_ready.status_code in (200, 503)
        assert "components" in res_ready.json()

        res_deps = await client.get("/health/dependencies")
        assert res_deps.status_code == 200
        assert "dependencies" in res_deps.json()
