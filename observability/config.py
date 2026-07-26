"""Structured logging and OpenTelemetry distributed tracing setup for ComplianceOS."""

import logging
from typing import Any, Optional, TYPE_CHECKING
from observability.logging import JSONLogFormatter, setup_logging

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

_tracer_provider: Optional[Any] = None


def setup_telemetry(service_name: str = "ComplianceOS") -> Optional[Any]:
    """Initialize OpenTelemetry TracerProvider and return configured Tracer."""
    global _tracer_provider
    if not OPENTELEMETRY_AVAILABLE:
        logging.warning(
            "opentelemetry package not installed. Telemetry fallback active."
        )
        return None

    if _tracer_provider is None:
        resource = Resource.create(
            {"service.name": service_name, "environment": "production"}
        )
        _tracer_provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        _tracer_provider.add_span_processor(processor)
        trace.set_tracer_provider(_tracer_provider)
        logging.info(
            f"OpenTelemetry TracerProvider initialized for service '{service_name}'"
        )

    return trace.get_tracer(service_name)


def get_tracer(module_name: str = "complianceos"):
    """Get named tracer instance for context propagation."""
    if OPENTELEMETRY_AVAILABLE:
        return trace.get_tracer(module_name)
    return None


__all__ = ["JSONLogFormatter", "setup_logging", "setup_telemetry", "get_tracer"]
