# API Specification — Version 1.4: Platform Reliability & Observability

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/metrics` | Prometheus metrics exposition endpoint |
| `GET` | `/healthz` | Kubernetes liveness probe |
| `GET` | `/readyz` | Kubernetes readiness probe |
