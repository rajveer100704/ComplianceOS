import sys
import json
import logging
from typing import Dict, Any


def get_current_otel_context():
    """Extracts trace_id and span_id from current OpenTelemetry span context if available."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            if ctx and ctx.is_valid:
                return {
                    "trace_id": f"{ctx.trace_id:032x}",
                    "span_id": f"{ctx.span_id:016x}",
                }
    except Exception:
        pass
    return {"trace_id": None, "span_id": None}


class JSONLogFormatter(logging.Formatter):
    """Formatter emitting correlation-rich structured JSON log records for production aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # OpenTelemetry trace & span context
        otel_ctx = get_current_otel_context()
        trace_id = getattr(record, "trace_id", None) or otel_ctx["trace_id"]
        span_id = getattr(record, "span_id", None) or otel_ctx["span_id"]
        if trace_id:
            log_data["trace_id"] = trace_id
        if span_id:
            log_data["span_id"] = span_id

        # Correlation and request context fields
        context_fields = [
            "request_id",
            "organization_id",
            "user_id",
            "session_id",
            "endpoint",
            "method",
            "status_code",
            "latency_ms",
            "path",
        ]
        for field in context_fields:
            val = getattr(record, field, None)
            if val is not None:
                log_data[field] = val

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO"):
    """Configures structured JSON logging for the application root logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter())
    root_logger.addHandler(handler)
