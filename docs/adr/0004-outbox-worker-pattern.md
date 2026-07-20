# ADR 0004: Asynchronous Processing via Outbox Pattern & Background Task Queue

**Date:** 2026-07-20  
**Status:** Accepted  
**Deciders:** Core Engineering Team  

---

## Context & Problem Statement
Heavy background operations (such as multi-page PDF parsing, vector embedding generation, review snapshot creation, and report export compilation) must not block HTTP request threads.

## Decision Outcome
**Chosen Option:** **Outbox Pattern + Async Task Queue Service**

### Positive Consequences
- **Reliable Event Dispatching**: Events written to `outbox_events` and tasks written to `tasks` table within the same transaction.
- **Asynchronous Exporters**: Document exports compiled in background worker tasks without blocking web API requests.

## Alternatives Rejected

- **Celery + RabbitMQ**: Rejected due to heavy broker dependency overhead for early platform iterations.
- **In-Memory Threading**: Rejected due to risk of silent task loss upon web process crashes or restarts.
