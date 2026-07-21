---
name: database-design
description: >
  Use when designing database schemas, creating Alembic migrations, adding indexes,
  defining constraints, managing foreign keys, handling transactions, and optimizing
  query performance. Covers SQLAlchemy ORM model design and migration lifecycle.
---

# Database Design Skill

## When to Use

- Creating new ORM models.
- Adding or modifying database columns, indexes, or constraints.
- Creating Alembic migrations.
- Designing foreign key relationships.
- Optimizing query performance.
- Implementing backwards-compatible schema changes.

## Workflow

1. **Design the schema** — Define tables, columns, types, constraints, indexes.
2. **Create ORM model** in `database/models/`.
3. **Generate migration**: `alembic revision --autogenerate -m "description"`.
4. **Review migration** — Verify auto-generated SQL is correct.
5. **Test migration up**: `alembic upgrade head`.
6. **Test migration down**: `alembic downgrade -1`.
7. **Create repository** for data access.
8. **Write tests** against SQLite in-memory database.

## ORM Model Convention

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from database.models.base import Base

class ComplianceRequest(Base):
    __tablename__ = "compliance_requests"

    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False)
    regulation_id = Column(String, ForeignKey("regulations.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    regulation = relationship("Regulation", back_populates="requests")
    claims = relationship("Claim", back_populates="request", cascade="all, delete-orphan")

    # Composite indexes
    __table_args__ = (
        Index("ix_requests_status_created", "status", "created_at"),
    )
```

## Rules

### Schema Design
- **Primary keys**: Use UUID strings (`str(uuid.uuid4())`), not auto-increment integers.
- **Timestamps**: Always `DateTime(timezone=True)`. Always store UTC.
- **String lengths**: Always specify `String(N)` with explicit max length.
- **Nullable**: Explicit `nullable=True/False` on every column.
- **Defaults**: Use `server_default` for database-level defaults where possible.

### Indexes
- Index columns used in `WHERE`, `ORDER BY`, and `JOIN`.
- Create composite indexes for common query patterns.
- Name indexes explicitly: `ix_<table>_<column>`.

### Foreign Keys
- Always define `ForeignKey` constraints.
- Use `CASCADE` for parent-child relationships.
- Use `SET NULL` for optional references.
- Never use `NO ACTION` — always specify behavior.

### Migrations
- Every schema change requires an Alembic migration.
- Never modify the database manually.
- Test both `upgrade` and `downgrade`.
- Backwards-compatible changes: add columns with defaults, add tables.
- Destructive changes: two-phase migration (add new → migrate data → remove old).

### Transactions
- Use Unit of Work (`database/transaction.py`) for transaction boundaries.
- Repositories use `flush()`, services use `commit()`.
- Never commit in repositories.

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md) §6 (Database Schema Evolution)
- [CODING_STANDARD.md](../../CODING_STANDARD.md) §5 (Repository Pattern)
- [PERFORMANCE.md](../../PERFORMANCE.md) §1 (Database Performance)
