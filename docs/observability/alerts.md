# Prometheus & Sentry Alert Rules — ComplianceOS

## Prometheus Alert Rules

```yaml
groups:
  - name: complianceos_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "ComplianceOS high HTTP 5xx error rate (>5%)"

      - alert: HighLatencyP95
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "ComplianceOS P95 response latency exceeded 2.0 seconds"

      - alert: OutboxQueueBacklog
        expr: outbox_queue_depth > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Outbox queue depth backed up (>100 pending events)"
```
