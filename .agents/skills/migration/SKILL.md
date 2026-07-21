---
name: migration
description: >
  Use when handling database schema changes, writing Alembic migrations, managing
  data backfills, enforcing backwards compatibility, and writing rollback scripts.
---

# Database Migration Skill

## When to Use

- Adding, altering, or dropping database tables or columns.
- Writing Alembic migration scripts.
- Executing multi-phase destructive schema modifications.
- Implementing data backfills and verifications.

## Migration Lifecycle

```
1. Model Update          → Modify SQLAlchemy models in database/models/
2. Generate Revision     → alembic revision --autogenerate -m "description"
3. Inspect Revision      → Manually verify generated upgrade() and downgrade()
4. Apply Migration       → python -m alembic upgrade head
5. Verify Rollback       → python -m alembic downgrade -1
6. Re-apply Migration    → python -m alembic upgrade head
7. Execute Data Backfill → (If needed) Run isolated backfill script
```

## Rules for Backwards Compatibility

1. **Additive First**: New columns must be `nullable=True` or have a server default.
2. **Two-Phase Destructive Changes**:
   - *Phase 1*: Add new column/table, write to both old and new structures, backfill historical rows.
   - *Phase 2* (Next Release): Switch reads to new structure, drop old column/table in a separate migration.
3. **Index Creation**: Create large indexes concurrently when possible to avoid lock timeouts.
4. **Data Backfills**: Execute heavy data transformations in batched background jobs, never inside DDL transactions.

## Checklist

- [ ] Migration file created in `database/migrations/versions/`.
- [ ] Both `upgrade()` and `downgrade()` methods are fully implemented.
- [ ] Tested against both SQLite and PostgreSQL engines.
- [ ] No table locking queries without timeouts.
- [ ] Tested `alembic upgrade head` and `alembic downgrade -1` cleanly.

## References

- [database-design](../database-design/SKILL.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md) §6
