import asyncio
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Response, status
from config.settings import settings

from observability.checkers.base import BaseHealthChecker, HealthResult
from observability.checkers.database import DatabaseChecker
from observability.checkers.qdrant import QdrantChecker
from observability.checkers.worker import WorkerChecker
from observability.checkers.storage import StorageChecker
from observability.checkers.integration import IntegrationChecker

logger = logging.getLogger("observability_health")

router = APIRouter(tags=["Health"])


class HealthService:
    """Aggregator executing modular dependency health checkers."""

    def __init__(self, checkers: Optional[List[BaseHealthChecker]] = None):
        self.checkers: List[BaseHealthChecker] = checkers or [
            DatabaseChecker(),
            QdrantChecker(),
            WorkerChecker(),
            StorageChecker(),
            IntegrationChecker(),
        ]

    async def run_checkers(self) -> Dict[str, HealthResult]:
        """Runs all checkers concurrently using asyncio.gather."""
        results = await asyncio.gather(
            *[checker.check() for checker in self.checkers],
            return_exceptions=True,
        )
        report: Dict[str, HealthResult] = {}
        for checker, res in zip(self.checkers, results):
            if isinstance(res, Exception):
                report[checker.name] = HealthResult(
                    name=checker.name,
                    healthy=False,
                    status="unhealthy",
                    latency_ms=0.0,
                    error=str(res),
                )
            else:
                report[checker.name] = res
        return report


health_service = HealthService()


@router.get("/healthz")
async def liveness_probe():
    """Kubernetes liveness probe testing process execution."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@router.get("/readyz")
async def readiness_probe(response: Response):
    """Kubernetes readiness probe verifying primary backend dependencies."""
    report = await health_service.run_checkers()
    is_ready = all(r.healthy for r in report.values())

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "degraded",
        "ready": is_ready,
        "components": {
            k: {
                "healthy": v.healthy,
                "status": v.status,
                "latency_ms": v.latency_ms,
                "error": v.error,
            }
            for k, v in report.items()
        },
    }


@router.get("/health/dependencies")
async def dependency_diagnostics():
    """Detailed operational diagnostics for backend dependencies."""
    report = await health_service.run_checkers()
    return {
        "service": "complianceos",
        "dependencies": {
            k: {
                "name": v.name,
                "healthy": v.healthy,
                "status": v.status,
                "latency_ms": v.latency_ms,
                "details": v.details,
                "error": v.error,
            }
            for k, v in report.items()
        },
    }
