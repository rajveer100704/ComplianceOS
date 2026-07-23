import time
import logging
from typing import Optional, Any
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings, Settings
from observability.logging import setup_logging
from observability.metrics import metrics_service
from observability.tracing import setup_tracing
from observability.sentry import setup_sentry

logger = logging.getLogger("observability_service")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware timing requests, logging correlation context, and recording Prometheus metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        # Extract correlation IDs
        request_id = request.headers.get("X-Request-ID") or getattr(
            request.state, "request_id", None
        )
        org_id = request.headers.get("X-Organization-Id") or getattr(
            request.state, "org_id", None
        )

        response: Response
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_s = time.perf_counter() - start_time
            metrics_service.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration_s=duration_s,
            )
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "organization_id": org_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": 500,
                    "latency_ms": round(duration_s * 1000.0, 2),
                },
                exc_info=True,
            )
            raise exc

        duration_s = time.perf_counter() - start_time
        latency_ms = round(duration_s * 1000.0, 2)

        # Record metrics
        metrics_service.record_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration_s=duration_s,
        )

        # Emit correlation-rich structured log
        if not request.url.path.startswith(("/metrics", "/healthz", "/readyz")):
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({latency_ms}ms)",
                extra={
                    "request_id": request_id,
                    "organization_id": org_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                },
            )

        return response


class ObservabilityService:
    """Unified operational facade initializing logging, metrics, tracing, Sentry, and middleware."""

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or settings

    def initialize(self, app: Optional[FastAPI] = None):
        """Sequential operational boot sequence."""
        # 1. Logging
        setup_logging(log_level=self.config.LOG_LEVEL)
        logger.info("Structured JSON logging initialized.")

        # 2. OpenTelemetry Tracing
        setup_tracing(
            app=app,
            service_name=self.config.OTEL_SERVICE_NAME,
            otlp_endpoint=self.config.OTEL_EXPORTER_OTLP_ENDPOINT,
            enabled=self.config.TRACING_ENABLED,
        )

        # 3. Sentry Error Tracking
        setup_sentry(
            dsn=self.config.SENTRY_DSN,
            environment=self.config.ENVIRONMENT,
        )

        # 4. Attach Observability Middleware
        if app is not None:
            app.add_middleware(ObservabilityMiddleware)
            logger.info("Observability HTTP middleware attached.")

        return self
