# Operational Incident Runbook — ComplianceOS

## Health Probes & Response Rules

### 1. `/healthz` Fails (Liveness Probe 500)
- **Cause**: Application main event loop unresponsive.
- **Action**: Restart application container (`docker compose restart app`).

### 2. `/readyz` Fails (Readiness Probe 530)
- **Cause**: Backend dependency unreachable (PostgreSQL, Qdrant, Workers).
- **Action**: Inspect `/health/dependencies` JSON for degraded component. Check container logs.

### 3. High Error Rate / Sentry Alerts
- **Cause**: Unhandled exception spiking.
- **Action**: Review trace ID in Sentry / Jaeger and check correlated logs in Grafana Loki.
