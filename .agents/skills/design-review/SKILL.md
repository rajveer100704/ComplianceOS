---
name: design-review
description: >
  Use before writing any code to review the design plan: answers architectural,
  reusability, migration, API, testing, and documentation impacts.
---

# Pre-Implementation Design Review Skill

## When to Use

- Before starting code implementation on any ticket or feature.
- To evaluate design impacts and prevent architectural mistakes before writing code.

## Key Questions to Answer Before Implementation

1. **Architecture Check**: Does this proposed change violate any layer constraints in `ARCHITECTURE.md`?
2. **Reusability Check**: Can this reuse an existing service, repository, model, or helper?
3. **Migration Check**: Is a database schema change or Alembic migration required?
4. **API Contract Check**: Does this alter any public API endpoints, schemas, or status codes?
5. **Testing Impact**: What unit, integration, and API tests are required for coverage?
6. **Documentation Impact**: What documentation files (`README.md`, `CHANGELOG.md`, API docs) must be updated?

## Checklist

- [ ] Architectural constraints verified.
- [ ] No duplicate functionality introduced.
- [ ] Migration strategy defined (if schema changes).
- [ ] API contract changes documented.
- [ ] Test plan created.
- [ ] Documentation requirements identified.

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [CODING_STANDARD.md](../../CODING_STANDARD.md)
