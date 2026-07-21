# ComplianceOS — Agent Development Guide

> **This file is the entry point for autonomous coding agents.**
> It provides a concise overview and routes to detailed specification documents.
> Keep this file under 500 lines. Load specialized skills and references on demand.

---

## 1. Project Overview

**ComplianceOS** is an enterprise AI regulatory compliance platform built on FastAPI.
It automates claim verification against engineering standards (FAA Part 450, NRC 10 CFR, ASME BPVC) using hybrid dense-lexical vector retrieval, and provides human-in-the-loop review workflows with versioned snapshots, structured report generation, and production operational monitoring.

**Repository**: [https://github.com/rajveer100704/ComplianceOS](https://github.com/rajveer100704/ComplianceOS)

---

## 2. Technology Stack

| Layer | Technology | Version |
| :--- | :--- | :--- |
| **Runtime** | Python | 3.11+ |
| **Web Framework** | FastAPI (ASGI, async) | ≥ 0.100 |
| **ORM** | SQLAlchemy 2.0 (async) | ≥ 2.0 |
| **Migrations** | Alembic | ≥ 1.11 |
| **Vector Database** | Qdrant | ≥ 1.7 |
| **Embeddings** | SentenceTransformers | ≥ 2.2 |
| **PDF Parsing** | PyMuPDF (fitz) | ≥ 1.23 |
| **OCR** | Tesseract via pytesseract | ≥ 0.3 |
| **Agent Orchestration** | LangGraph | ≥ 0.0.30 |
| **Validation** | Pydantic v2 | ≥ 2.0 |
| **Settings** | pydantic-settings | ≥ 2.0 |
| **HTTP Client** | httpx (async) | ≥ 0.24 |
| **Metrics** | prometheus-client | ≥ 0.17 |
| **Container** | Docker + Docker Compose | — |
| **CI** | GitHub Actions | — |

### Approved Libraries

Do not introduce new dependencies without explicit justification in an ADR.
The following are pre-approved:

- Standard library modules
- All packages listed in `requirements.txt`
- `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-benchmark` (test only)
- `black`, `ruff`, `mypy` (lint/type-check only)

---

## 3. Repository Layout & Layer Ownership

```
ComplianceOS/
│
├── main.py                    # FastAPI app factory, route registration
├── pipeline.py                # LangGraph compliance pipeline
├── db.py                      # Legacy DB bootstrap (SQLite fallback)
├── index.html                 # 3-Pane Review Workstation SPA
│
├── auth/                      # 🔐 Authentication & Authorization
│   ├── providers/             #    Auth provider implementations (API Key, JWT)
│   ├── dependencies.py        #    FastAPI Depends() for auth injection
│   ├── middleware.py           #    Security headers middleware
│   └── middleware_request_id.py #   X-Request-ID propagation
│
├── config/                    # ⚙️ Application Configuration
│   └── settings.py            #    Pydantic settings (env vars / .env)
│
├── database/                  # 🗄️ Persistence Layer
│   ├── models/                #    SQLAlchemy ORM models
│   ├── repositories/          #    Data access (Repository pattern)
│   ├── services/              #    Database-level services
│   ├── engine.py              #    Async engine factory
│   ├── session.py             #    Scoped async session factory
│   ├── transaction.py         #    Unit of Work implementation
│   └── migrations/            #    Alembic migration scripts
│
├── retrieval/                 # 🔍 Vector Retrieval Engine
│   ├── retrievers/            #    Dense, BM25, Hybrid retrievers
│   ├── rerankers/             #    Cross-encoder, cosine rerankers
│   ├── embeddings/            #    Embedding model management
│   ├── stores/                #    Qdrant vector store adapters
│   ├── pipeline/              #    Retrieval pipeline orchestration
│   ├── evaluation/            #    Recall, MRR, precision metrics
│   └── container.py           #    Retrieval dependency container
│
├── review/                    # 📋 Human Review Domain
│   ├── repositories/          #    Review data access
│   ├── services/              #    Review business logic
│   ├── receipts/              #    Immutable transition receipts
│   └── events.py              #    Domain event definitions
│
├── report/                    # 📊 Report Generation Domain
│   ├── repositories/          #    Report data access
│   └── exporters/             #    HTML, Markdown, JSON exporters
│
├── worker/                    # ⚡ Background Worker System
│   ├── backends/              #    Local, ARQ, Future backends
│   ├── dispatcher.py          #    Outbox event dispatcher
│   ├── scheduler.py           #    Job scheduler
│   └── heartbeat.py           #    Worker health monitoring
│
├── parsers/                   # 📄 Document Parsing
│   ├── factory.py             #    Parser factory
│   ├── registry.py            #    Parser registry
│   └── pymupdf_parser.py      #    PyMuPDF + OCR parser
│
├── observability/             # 📈 Monitoring & Metrics
│   └── config.py              #    Structured logging setup
│
├── storage/                   # 💾 File Storage Abstraction
│
├── tests/                     # 🧪 Test Suite
├── test_main.py               #    Primary API + integration tests
│
├── docs/                      # 📚 Documentation
│   ├── adr/                   #    Architecture Decision Records
│   ├── security/              #    Security engineering rules
│   ├── images/                #    Screenshots & diagrams
│   ├── deployment-guide.md
│   └── runtime-validation.md
│
├── roadmap/                   # 🗺️ Version Implementation Packages
│   ├── v1.1-auth/
│   ├── v1.2-multitenant/
│   ├── v1.3-integrations/
│   ├── v1.4-observability/
│   ├── v1.5-policy-engine/
│   └── v2.0-ai-platform/
│
├── .agents/skills/            # 🤖 Agent Skill Definitions
│
├── AGENTS.md                  # ← You are here
├── ARCHITECTURE.md            # Layer constraints & domain map
├── CODING_STANDARD.md         # Naming, patterns, conventions
├── TESTING.md                 # Test pyramid & coverage rules
├── PERFORMANCE.md             # Performance engineering rules
├── ROADMAP.md                 # Semantic versioning release plan
├── CONTRIBUTING.md            # Contributor guide
├── SECURITY.md                # Public vulnerability policy
├── LICENSE                    # MIT License
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 4. Architecture Constraints

> **Full specification**: See [ARCHITECTURE.md](ARCHITECTURE.md)

### Hard Rules

1. **Router → Service → Repository → ORM/Qdrant**. Never skip layers.
2. **No business logic in routers.** Routers validate input and delegate to services.
3. **No ORM access from routers.** Only repositories touch SQLAlchemy models.
4. **No Qdrant calls from routers.** Only retrieval services access vector stores.
5. **No embedding creation in routers.** Embeddings are managed by the retrieval layer.
6. **Workers only process queued jobs.** Workers read from the outbox, never from HTTP.
7. **No circular imports.** If module A imports B, module B must not import A.
8. **Services own business logic.** All domain rules live in the service layer.
9. **Repositories are data access only.** No business decisions in repository methods.
10. **Unit of Work wraps transactions.** Never commit/rollback outside `transaction.py`.

---

## 5. Coding Rules

> **Full specification**: See [CODING_STANDARD.md](CODING_STANDARD.md)

### Summary

- **Naming**: `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE` constants.
- **Typing**: Every function signature must have type annotations. No `Any` unless unavoidable.
- **DI**: Use FastAPI `Depends()` for all injectable dependencies.
- **DTOs**: Pydantic `BaseModel` for all request/response schemas. Never expose ORM models in API responses.
- **Errors**: Raise domain-specific exceptions from services. Routers catch and convert to `HTTPException`.
- **Logging**: Structured JSON via `observability/config.py`. **Never log secrets, tokens, or PII.**
- **Imports**: Group as stdlib → third-party → project modules. One blank line between groups.

---

## 6. Quality Gates

All code must pass these checks before merge:

| Gate | Tool | Command | Blocking |
| :--- | :--- | :--- | :--- |
| Formatting | Black | `black --check .` | ✅ Yes |
| Linting | Ruff | `ruff check .` | ⚠️ Advisory |
| Type Checking | MyPy | `mypy .` | ⚠️ Advisory |
| Tests | pytest | `pytest --cov --cov-report=xml` | ✅ Yes |
| Coverage | pytest-cov | Threshold: ≥ 80% | ✅ Yes |
| Docker | Docker | `docker build .` | ✅ Yes |

---

## 7. Git Workflow

### Branch Naming

```
feat/<short-description>      # New features
fix/<short-description>       # Bug fixes
docs/<short-description>      # Documentation only
refactor/<short-description>  # Code restructuring
chore/<short-description>     # Maintenance tasks
```

### Conventional Commits

```
feat: add Google OAuth2 login flow
fix: prevent refresh token replay attack
docs: update deployment guide for Railway
refactor: extract JWT signing into dedicated service
chore: upgrade actions/checkout to v4
build: add langgraph to requirements.txt
test: add integration tests for OAuth callback
```

---

## 8. Definition of Done

A feature is **done** when:

- [ ] Feature implemented following architecture constraints.
- [ ] Unit tests written and passing.
- [ ] Integration tests written and passing.
- [ ] API tests written and passing (if endpoint changes).
- [ ] Black formatting passes.
- [ ] No new Ruff errors introduced.
- [ ] Documentation updated (README, API docs, ADR if applicable).
- [ ] OpenAPI schema reflects changes (if endpoints changed).
- [ ] Docker image builds successfully.
- [ ] CHANGELOG updated.
- [ ] Conventional commit message used.

---

## 9. Prohibitions

The agent must **never**:

1. Break existing public API contracts without documenting the change in an ADR.
2. Remove tests to make CI pass.
3. Reduce test coverage below the threshold.
4. Introduce duplicate implementations of existing functionality.
5. Add new dependencies without justification.
6. Skip Alembic migrations when changing the database schema.
7. Store secrets, tokens, or passwords in plaintext.
8. Log secrets, API keys, bearer tokens, or PII.
9. Use string interpolation in SQL queries (parameterized only).
10. Commit `.env`, `compliance.db`, `__pycache__/`, or `venv/`.

---

## 10. Feature Development Workflow

Every feature implementation follows this sequence:

```
1. Read PRD           → roadmap/v*.*/PRD.md
2. Read ADR           → roadmap/v*.*/ADR.md
3. Read API Contract  → roadmap/v*.*/API.md
4. Read DB Design     → roadmap/v*.*/DATABASE.md
5. Read Architecture  → ARCHITECTURE.md
6. Plan               → Create implementation steps
7. Implement          → Backend → Frontend → Tests
8. Run Tests          → pytest + coverage
9. Run Lint           → black + ruff + mypy
10. Review            → Self-check against ARCHITECTURE.md
11. Update Docs       → README, CHANGELOG, API docs
12. Commit            → Conventional commit, push
```

---

## 11. Detailed Specification Documents

| Document | Purpose |
| :--- | :--- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layer constraints, domain ownership, extension points |
| [CODING_STANDARD.md](CODING_STANDARD.md) | Naming, patterns, DI, error handling, logging |
| [TESTING.md](TESTING.md) | Test pyramid, coverage, fixtures, mocking |
| [PERFORMANCE.md](PERFORMANCE.md) | N+1, batching, async, streaming, pagination |
| [docs/security/SECURITY_ENGINEERING.md](docs/security/SECURITY_ENGINEERING.md) | JWT, OAuth, encryption, OWASP, secrets |
| [ROADMAP.md](ROADMAP.md) | Semantic versioning release plan |

---

## 12. Agent Skills

Specialized skills are available in `.agents/skills/`. Each skill contains a `SKILL.md` with YAML frontmatter and workflow instructions. Skills are loaded automatically when relevant to the current task.

| Skill | Domain |
| :--- | :--- |
| `architecture-review` | Validate changes against layer constraints |
| `fastapi-backend` | Backend route, service, repository implementation |
| `oauth` | OAuth2, JWT, session, refresh token flows |
| `oauth-security` | OAuth-specific security (PKCE, state, replay) |
| `application-security` | General application security (OWASP, XSS, CSRF) |
| `database-design` | Alembic, indexes, constraints, normalization |
| `multitenancy` | Organization, team, tenant isolation |
| `integrations` | Slack, Jira, GitHub, S3/R2 connectors |
| `observability` | OpenTelemetry, Jaeger, Grafana, Sentry |
| `policy-engine` | Rule engine, approval gates, escalation |
| `performance` | N+1, batching, streaming, caching |
| `testing` | Test pyramid, coverage, fixtures, mocking |
| `api-review` | REST conventions, status codes, pagination |
| `frontend-ux` | Accessibility, loading states, responsiveness |
| `adr` | Architecture Decision Record generation |
| `migration` | Schema changes, backwards compatibility, rollback |
| `documentation` | Documentation update checklist |
| `release` | Pre-release checklist, git tag, CHANGELOG |
| `feature-development` | End-to-end feature implementation workflow |
