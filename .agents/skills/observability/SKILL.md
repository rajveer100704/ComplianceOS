---
name: observability
description: >
  Use when implementing production observability: OpenTelemetry instrumentation,
  Jaeger distributed tracing, Prometheus metrics, Grafana dashboards, Sentry error
  tracking, structured log correlation, and health check dashboards.
---

# Observability Skill

## When to Use

- Adding OpenTelemetry instrumentation.
- Configuring distributed tracing with Jaeger.
- Creating Prometheus metrics and Grafana dashboards.
- Setting up Sentry error capture.
- Correlating logs with request IDs and trace IDs.

## Observability Stack

```
Application (FastAPI)
       │
       ├── OpenTelemetry SDK
       │   ├── Traces → OTLP Exporter → Jaeger
       │   ├── Metrics → Prometheus Exporter → Grafana
       │   └── Logs → Structured JSON → Log Aggregator
       │
       ├── Sentry SDK
       │   └── Exceptions → Sentry Dashboard
       │
       └── Prometheus Client
           └── /metrics endpoint → Grafana
```

## Implementation Rules

### Tracing
- Instrument all HTTP handlers automatically via OpenTelemetry FastAPI middleware.
- Create custom spans for: database queries, Qdrant operations, external HTTP calls, document parsing.
- Propagate trace context (`traceparent` header) across service boundaries.
- Include `request_id` as a span attribute for correlation.

### Metrics
- **Counter**: `requests_total`, `errors_total`, `claims_processed_total`.
- **Histogram**: `request_duration_seconds`, `retrieval_latency_seconds`, `parse_duration_seconds`.
- **Gauge**: `active_workers`, `outbox_queue_depth`, `active_sessions`.
- Expose at `/metrics` in Prometheus exposition format.

### Logging
- Structured JSON via `observability/config.py`.
- Include in every log: `request_id`, `trace_id`, `span_id`, `timestamp`, `level`.
- Never log: secrets, tokens, PII, full request/response bodies.

### Error Tracking
- Capture unhandled exceptions to Sentry.
- Include user context (role, not PII).
- Include request context (endpoint, method, status code).
- Set environment tag (development/staging/production).

### Health Checks
- `/healthz` — Liveness probe (is the process running?).
- `/readyz` — Readiness probe (are dependencies connected?).
- `/metrics` — Prometheus metrics endpoint.

## Key Dashboards

| Dashboard | Panels |
| :--- | :--- |
| **API Performance** | P50/P95/P99 latency, request rate, error rate |
| **Retrieval Pipeline** | Search latency, recall@5, MRR, reranker latency |
| **Worker Health** | Queue depth, processing rate, failure rate, heartbeat |
| **Database** | Query latency, connection pool usage, slow queries |
| **System** | CPU, memory, disk, network |

## References

- [PERFORMANCE.md](../../PERFORMANCE.md) §9 (Performance Monitoring)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
