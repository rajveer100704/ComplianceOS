# OpenTelemetry Tracing Specification — ComplianceOS

## Trace Propagation

Traces propagate via standard W3C `traceparent` HTTP headers across service boundaries.

## Span Hierarchy

```
HTTP POST /api/v1/claims/verify
└── vector_retrieval
    ├── qdrant_search
    └── rerank_candidates
└── persist_verdict
└── outbox_dispatch_event
```

## Decorator Usage

Use `@trace_span("span_name")` to instrument critical functions:
```python
from observability.tracing import trace_span

@trace_span("execute_hybrid_retrieval")
async def retrieve_regulations(claim_text: str):
    ...
```
