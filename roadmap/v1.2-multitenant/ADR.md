# ADR 0006: Tenant-Scoped Shared Database Schema Isolation

## Date: 2026-07-21
## Status: Accepted

## Context & Decision
We chose **Shared Database with Column-Based Tenant Isolation (`organization_id`)** over Database-per-Tenant or Schema-per-Tenant.

## Rationale
Column-based isolation provides optimal resource utilization, simplifies Alembic migrations, and supports thousands of tenants on shared PostgreSQL instances without connection pool exhaustion.
