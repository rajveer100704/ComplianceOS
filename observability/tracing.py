import logging
import functools
from typing import Optional, Callable, Any

logger = logging.getLogger("observability_tracing")

_TRACER = None


def setup_tracing(
    app: Any = None,
    service_name: str = "complianceos-api",
    otlp_endpoint: Optional[str] = None,
    enabled: bool = True,
):
    """Configures OpenTelemetry tracer provider, OTLP exporter, and FastAPI instrumentation."""
    global _TRACER

    if not enabled:
        logger.info("OpenTelemetry tracing disabled by configuration.")
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME

        resource = Resource.create({SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)

        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )

                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(
                    f"OpenTelemetry OTLP gRPC exporter configured -> {otlp_endpoint}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize OTLP gRPC exporter ({e}), falling back to console exporter."
                )
                provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        else:
            logger.info(
                "OpenTelemetry unconfigured OTLP endpoint; using in-memory tracer provider."
            )

        trace.set_tracer_provider(provider)
        _TRACER = trace.get_tracer(service_name)

        if app is not None:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

                FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
                logger.info("FastAPI OpenTelemetry instrumentation attached.")
            except Exception as e:
                logger.warning(f"Could not instrument FastAPI application: {e}")

        return _TRACER

    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed. Tracing spans will execute as no-ops."
        )
        return None
    except Exception as e:
        logger.error(f"Error setting up OpenTelemetry tracing: {e}")
        return None


def get_tracer():
    """Returns the globally configured OpenTelemetry tracer or a no-op fallback."""
    global _TRACER
    if _TRACER is not None:
        return _TRACER
    try:
        from opentelemetry import trace

        return trace.get_tracer("complianceos-fallback")
    except Exception:
        return None


def trace_span(name: str):
    """Decorator creating a named OpenTelemetry trace span around a function execution."""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if tracer:
                with tracer.start_as_current_span(name):
                    return await func(*args, **kwargs)
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if tracer:
                with tracer.start_as_current_span(name):
                    return func(*args, **kwargs)
            return func(*args, **kwargs)

        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
