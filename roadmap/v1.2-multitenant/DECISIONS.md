# Architectural Decisions Log — Version 1.2: Multi-Tenant SaaS Architecture

- **Decision 1**: Column-level `organization_id` isolation for all domain entities.
- **Decision 2**: Shared Qdrant collection with payload filters (`organization_id == X`).
