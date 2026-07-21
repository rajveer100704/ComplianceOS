# ComplianceOS Architecture

This document defines the architectural constraints, layer boundaries, domain ownership, and extension points for ComplianceOS. Every code change must conform to these rules.

---

## 1. Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HTTP / WebSocket                              │
│                          (FastAPI ASGI Server)                              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ROUTER LAYER                                     │
│                                                                             │
│  Responsibilities:                                                          │
│  • Request validation (Pydantic models)                                     │
│  • Authentication injection (Depends)                                       │
│  • HTTP status code mapping                                                 │
│  • Response serialization                                                   │
│                                                                             │
│  Prohibitions:                                                              │
│  ✗ No business logic                                                        │
│  ✗ No direct database access                                                │
│  ✗ No direct Qdrant access                                                  │
│  ✗ No embedding creation                                                    │
│  ✗ No transaction management                                                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ Depends()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                    │
│                                                                             │
│  Responsibilities:                                                          │
│  • Business logic and domain rules                                          │
│  • Input validation beyond DTO constraints                                  │
│  • Transaction boundary management                                          │
│  • Domain event emission                                                    │
│  • Orchestrating multiple repositories                                      │
│  • Authorization enforcement                                                │
│                                                                             │
│  Prohibitions:                                                              │
│  ✗ No HTTP-specific logic (status codes, headers)                           │
│  ✗ No direct ORM model construction for responses                           │
│  ✗ No calling other services' repositories directly                         │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REPOSITORY LAYER                                   │
│                                                                             │
│  Responsibilities:                                                          │
│  • Data access (CRUD operations)                                            │
│  • Query construction (SQLAlchemy selects)                                   │
│  • Qdrant vector operations                                                 │
│  • Result mapping                                                           │
│                                                                             │
│  Prohibitions:                                                              │
│  ✗ No business logic                                                        │
│  ✗ No transaction commits (use flush)                                       │
│  ✗ No domain event emission                                                 │
│  ✗ No calling other repositories                                            │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                                 │
│                                                                             │
│  • SQLAlchemy ORM Models (database/models/)                                 │
│  • Qdrant Client (retrieval/stores/)                                        │
│  • File Storage (storage/)                                                  │
│  • External HTTP APIs (httpx)                                               │
│  • Message Queue / Outbox (worker/)                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hard Constraints

These rules are **non-negotiable**. Any code that violates them must be rejected.

### Layer Violations

| Rule | Violation Example | Correct Approach |
| :--- | :--- | :--- |
| Router must not access DB | `session.execute(select(...))` in router | Call service method |
| Router must not call Qdrant | `qdrant_client.search(...)` in router | Call retrieval service |
| Router must not create embeddings | `model.encode(...)` in router | Call retrieval service |
| Repository must not commit | `session.commit()` in repository | Use `flush()`, service commits |
| Repository must not contain business logic | `if claim.status == "approved"` in repo | Move check to service |
| Service must not return HTTP responses | `return JSONResponse(...)` in service | Return DTO, router wraps |
| Worker must not handle HTTP | Direct FastAPI request in worker | Worker reads outbox queue |

### Dependency Direction

```
Router  →  Service  →  Repository  →  ORM / Qdrant
  ↓
Middleware  →  Config / Settings
```

**Never reverse the arrow.** A repository must never import from a service. A service must never import from a router.

### Circular Import Prevention

- If module A imports module B, module B must **never** import module A.
- Use dependency injection or event-based communication to break cycles.
- Domain events (`review/events.py`) are the preferred decoupling mechanism.

---

## 3. Domain Ownership

Each domain owns its models, repositories, services, and events. Cross-domain communication happens through the service layer or domain events.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Review     │    │   Report     │    │  Retrieval   │
│   Domain     │    │   Domain     │    │   Domain     │
│              │    │              │    │              │
│ • Claims     │    │ • Reports    │    │ • Embeddings │
│ • Decisions  │◄──►│ • Snapshots  │◄──►│ • Vectors    │
│ • Comments   │    │ • Exporters  │    │ • Rerankers  │
│ • Evidence   │    │ • Templates  │    │ • Chunkers   │
│ • Pins       │    │ • Risk Matrix│    │ • Pipeline   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────┴───────┐
                    │   Database   │
                    │   Domain     │
                    │              │
                    │ • Engine     │
                    │ • Session    │
                    │ • Migrations │
                    │ • Unit of Wk │
                    └──────────────┘
```

### Domain Boundaries

| Domain | Owns | Must Not Access Directly |
| :--- | :--- | :--- |
| **Review** | Claims, decisions, comments, evidence pins | Report exporters, vector stores |
| **Report** | Reports, snapshots, templates, exporters | Review decision logic, embeddings |
| **Retrieval** | Embeddings, vectors, rerankers, chunkers | Review state, report templates |
| **Database** | Engine, session, migrations, Unit of Work | Any domain-specific logic |
| **Worker** | Job queue, dispatcher, heartbeat | HTTP request handling |
| **Auth** | Providers, middleware, RBAC | Domain business logic |
| **Parsers** | Document parsing, OCR, registry | Review workflow, report generation |
| **Observability** | Logging, metrics, tracing | Business logic |
| **Config** | Settings, environment variables | Everything (config is read-only) |

---

## 4. Event Bus & Outbox Pattern

Cross-domain side effects are triggered through domain events and the outbox pattern.

```
Service emits event
       │
       ▼
┌──────────────┐
│   Outbox     │    Events are written to the outbox table
│   Table      │    within the same transaction as the
│              │    primary business operation.
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Worker     │    The background worker polls the outbox,
│   Dispatcher │    dequeues events, and dispatches to
│              │    registered handlers.
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Handler    │    Event handlers execute side effects
│              │    (e.g., generate embeddings, compile
│              │    reports, send notifications).
└──────────────┘
```

### Rules

- **Events are immutable.** Once written to the outbox, they are never modified.
- **Handlers are idempotent.** Processing the same event twice must produce the same result.
- **Handlers must not throw unhandled exceptions.** Failed events are retried with backoff.
- **Events carry data, not behavior.** The handler decides what to do.

---

## 5. Extension Points

### Adding a New Auth Provider

1. Create a new class in `auth/providers/` implementing the `authenticate()` method.
2. Register it in `auth/dependencies.py` → `get_auth_provider()`.
3. Add the provider name to `config/settings.py` → `AUTH_PROVIDER` field.
4. Write unit tests.

### Adding a New Report Exporter

1. Create a new exporter in `report/exporters/`.
2. Register it in the exporter factory.
3. Add the format to the export API endpoint.
4. Write unit tests.

### Adding a New Retriever

1. Create a new retriever in `retrieval/retrievers/`.
2. Register it in `retrieval/registry.py`.
3. Configure selection logic in `retrieval/selector.py`.
4. Write evaluation metrics tests.

### Adding a New Parser

1. Create a new parser in `parsers/` implementing `BaseParser`.
2. Register it in `parsers/registry.py`.
3. Update `parsers/factory.py` to route by file extension.
4. Write unit tests with sample documents.

### Adding a New Domain

1. Create the domain directory: `<domain>/models/`, `<domain>/repositories/`, `<domain>/services/`.
2. Create ORM models in `database/models/`.
3. Create Alembic migration: `alembic revision --autogenerate -m "add <domain> tables"`.
4. Register API routes in `main.py`.
5. Write ADR documenting the decision.
6. Write tests covering repository, service, and API layers.

---

## 6. Database Schema Evolution

- **Every schema change requires an Alembic migration.** Never modify the database manually.
- **Migrations must be backwards-compatible.** Use additive changes (new columns with defaults, new tables) when possible.
- **Destructive changes** (column removal, type changes) require a two-phase migration:
  1. Add new structure, migrate data.
  2. Remove old structure in a subsequent release.
- **Test migrations** both up and down: `alembic upgrade head` and `alembic downgrade -1`.

---

## 7. API Design Principles

- **RESTful resource naming**: `/claims`, `/claims/{id}`, `/claims/{id}/comments`.
- **Consistent HTTP methods**: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE (remove).
- **Consistent status codes**: 200 (OK), 201 (Created), 204 (No Content), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 422 (Validation Error), 429 (Rate Limited), 500 (Internal Error).
- **Pagination on all list endpoints**: Use `?page=1&page_size=50` with response metadata.
- **Filtering and sorting**: Use query parameters (`?status=pending&sort=created_at`).
- **Versioning**: Reserved for future use. Currently all endpoints are v1 (implicit).
