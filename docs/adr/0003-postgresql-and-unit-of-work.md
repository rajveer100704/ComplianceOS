# ADR 0003: Relational Persistence with PostgreSQL, Async SQLAlchemy & Unit of Work

**Date:** 2026-07-20  
**Status:** Accepted  
**Deciders:** Core Engineering Team  

---

## Context & Problem Statement
ComplianceOS requires transactional integrity across multi-entity writes (e.g. creating requests, claims, review activity logs, snapshots, and reports in a single atomic transaction).

## Decision Outcome
**Chosen Option:** **PostgreSQL + Async SQLAlchemy ORM + Unit of Work Pattern**

### Positive Consequences
- **Atomic Transactions**: `UnitOfWork` context manager handles explicit `commit()` and automatic `rollback()` on exceptions.
- **Alembic Schema Migrations**: Managed relational schema evolution supporting both PostgreSQL and local SQLite fallback during dev/testing.

## Alternatives Rejected

- **MongoDB / NoSQL**: Rejected due to lack of relational foreign key constraints and acid guarantees across multi-entity compliance review workflows.
- **Raw SQL Queries**: Rejected to prevent SQL injection vulnerabilities and maintain database driver portability.
