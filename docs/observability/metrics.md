# Prometheus Metrics Catalog — ComplianceOS

| Metric Name | Type | Description | Labels |
| :--- | :--- | :--- | :--- |
| `http_requests_total` | Counter | Total HTTP requests | `method`, `endpoint`, `status_code` |
| `http_request_duration_seconds` | Histogram | Request latency | `method`, `endpoint` |
| `active_sessions_count` | Gauge | Active user sessions | - |
| `retrieval_duration_seconds` | Histogram | Search latency | `search_type` |
| `retrieval_cache_hits_total` | Counter | Cache hits | - |
| `retrieval_cache_misses_total` | Counter | Cache misses | - |
| `outbox_queue_depth` | Gauge | Pending outbox jobs | - |
| `integration_dispatch_total` | Counter | Dispatches | `provider` |
| `integration_dispatch_failures_total` | Counter | Dispatch errors | `provider` |
