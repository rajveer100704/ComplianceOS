"""Observability package re-exporting key facades and services."""

from observability.service import ObservabilityService
from observability.metrics import metrics_service, MetricsService
from observability.tracing import setup_tracing, get_tracer, trace_span
from observability.logging import setup_logging, JSONLogFormatter
from observability.health import health_service, HealthService

__all__ = [
    "ObservabilityService",
    "metrics_service",
    "MetricsService",
    "setup_tracing",
    "get_tracer",
    "trace_span",
    "setup_logging",
    "JSONLogFormatter",
    "health_service",
    "HealthService",
]
