# ADR 0002: Adoption of FastAPI & Async ASGI Application Stack

**Date:** 2026-07-20  
**Status:** Accepted  
**Deciders:** Core Engineering Team  

---

## Context & Problem Statement
The ComplianceOS application platform requires high throughput API request handling, automated OpenAPI schema generation, async database I/O, and middleware support for security headers, request tracing (`X-Request-ID`), and RBAC dependency injection.

## Decision Outcome
**Chosen Option:** **FastAPI (Python 3.11 / Uvicorn)**

### Positive Consequences
- **Native Async I/O**: Asynchronous handling of SQLAlchemy sessions and HTTP client calls.
- **OpenAPI Schema Generation**: Automatic interactive API documentation generated at `/docs` and `/redoc`.
- **Dependency Injection**: Modular role authorization (`require_role("Reviewer" | "Lead Reviewer" | "Admin")`) via `fastapi.Depends`.

## Alternatives Rejected

- **Flask**: Rejected due to WSGI synchronous blocking model and lack of native async database session support.
- **Django**: Rejected due to monolithic ORM overhead and heavyweight default components for what is primarily a microservices REST API.
