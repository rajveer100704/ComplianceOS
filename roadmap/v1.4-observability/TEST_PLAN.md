# Test Plan — Version 1.4: Platform Reliability & Observability

- `test_metrics_endpoint_exposes_prometheus_format()`: Query `/metrics` and verify counter/histogram headers.
- `test_request_id_propagates_in_trace_spans()`: Verify active trace span includes `request_id` attribute.
