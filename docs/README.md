# ComplianceOS Documentation Hub

Welcome to the ComplianceOS documentation directory. This folder contains technical design specifications, architecture decision records (ADRs), deployment guides, security engineering rules, and operational validation runbooks.

---

## Documentation Index

| Document | Description | Target Audience |
| :--- | :--- | :--- |
| 📖 **[Deployment Guide](deployment-guide.md)** | Topology, cloud stack recommendations, env vars, CI/CD pipeline, and post-deployment smoke tests. | DevOps / SRE / Cloud Engineers |
| 📋 **[Operational Validation Runbook](runtime-validation.md)** | Empirical runtime verification protocol, test dataset specification, and evidence log template. | Compliance Auditors / Lead Reviewers |
| 🏛️ **[Architecture Decision Records (ADRs)](adr/)** | Technical design trade-offs and decisions for vector storage, async frameworks, ORMs, and background workers. | Software Architects / Tech Leads |
| 🔒 **[Security Engineering Rules](security/SECURITY_ENGINEERING.md)** | Internal JWT, OAuth, secrets, injection prevention, rate limiting, headers, CORS, PII, and STRIDE threat model. | Security Engineers / Backend Developers |

---

## Engineering Specification Documents (Root)

| Document | Description |
| :--- | :--- |
| 🤖 **[AGENTS.md](../AGENTS.md)** | Agent entry point — project overview, tech stack, repository map, quality gates, and skill index. |
| 🏗️ **[ARCHITECTURE.md](../ARCHITECTURE.md)** | Layer constraints, domain ownership, extension points, event bus contract, and API design principles. |
| 📝 **[CODING_STANDARD.md](../CODING_STANDARD.md)** | Naming conventions, import order, DTO rules, DI patterns, repository contract, service layer, error handling, logging, and async rules. |
| 🧪 **[TESTING.md](../TESTING.md)** | Test pyramid, coverage thresholds, fixture conventions, mocking rules, async testing, and performance benchmarks. |
| ⚡ **[PERFORMANCE.md](../PERFORMANCE.md)** | N+1 prevention, async rules, batch embeddings, streaming uploads, pagination, caching, connection management, and monitoring targets. |
| 🗺️ **[ROADMAP.md](../ROADMAP.md)** | Semantic versioning release plan (v1.0.0 → v2.0.0). |

---

## Architecture Decision Records (ADRs)

- **[ADR 0001: Selection of Qdrant as Primary Vector Database Engine](adr/0001-use-qdrant-vector-database.md)**
- **[ADR 0002: Adoption of FastAPI & Async ASGI Application Stack](adr/0002-fastapi-async-framework.md)**
- **[ADR 0003: Relational Persistence with PostgreSQL, Async SQLAlchemy & Unit of Work](adr/0003-postgresql-and-unit-of-work.md)**
- **[ADR 0004: Asynchronous Processing via Outbox Pattern & Background Task Queue](adr/0004-outbox-worker-pattern.md)**
