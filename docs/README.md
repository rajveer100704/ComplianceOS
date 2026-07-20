# ComplianceOS Documentation Hub

Welcome to the ComplianceOS documentation directory. This folder contains technical design specifications, architecture decision records (ADRs), deployment guides, and operational validation runbooks.

---

## Documentation Index

| Document | Description | Target Audience |
| :--- | :--- | :--- |
| 📖 **[Deployment Guide](deployment-guide.md)** | Topology, cloud stack recommendations, env vars, CI/CD pipeline, and post-deployment smoke tests. | DevOps / SRE / Cloud Engineers |
| 📋 **[Operational Validation Runbook](runtime-validation.md)** | Empirical runtime verification protocol, test dataset specification, and evidence log template. | Compliance Auditors / Lead Reviewers |
| 🏛️ **[Architecture Decision Records (ADRs)](adr/)** | Technical design trade-offs and decisions for vector storage, async frameworks, ORMs, and background workers. | Software Architects / Tech Leads |

---

## Architecture Decision Records (ADRs)

- **[ADR 0001: Selection of Qdrant as Primary Vector Database Engine](adr/0001-use-qdrant-vector-database.md)**
- **[ADR 0002: Adoption of FastAPI & Async ASGI Application Stack](adr/0002-fastapi-async-framework.md)**
- **[ADR 0003: Relational Persistence with PostgreSQL, Async SQLAlchemy & Unit of Work](adr/0003-postgresql-and-unit-of-work.md)**
- **[ADR 0004: Asynchronous Processing via Outbox Pattern & Background Task Queue](adr/0004-outbox-worker-pattern.md)**
