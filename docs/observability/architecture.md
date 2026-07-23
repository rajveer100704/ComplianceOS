# Observability Architecture — ComplianceOS

## Overview

ComplianceOS implements a 5-pillar production observability stack:
1. **Logging**: Correlation-rich structured JSON logs (compatible with Promtail & Loki).
2. **Metrics**: Prometheus client exposition endpoint (`/metrics`) backed by `MetricsService`.
3. **Tracing**: OpenTelemetry distributed tracing exported via OTLP gRPC/HTTP to Jaeger.
4. **Health Diagnostics**: Modular `HealthCheck` framework exposing `/healthz`, `/readyz`, and `/health/dependencies`.
5. **Error Tracking**: Automated exception capture and scope tagging via Sentry SDK.

## Unified Initialization

The application initializes observability using a single facade:
```python
from observability import ObservabilityService
from config.settings import settings

ObservabilityService(settings).initialize(app)
```
