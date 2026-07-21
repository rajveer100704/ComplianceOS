---
name: architecture-review
description: >
  Use when validating any proposed code change against ComplianceOS architecture constraints.
  Checks layer violations, dependency direction, circular imports, domain boundaries,
  and extension point compliance. Activate before merging any PR or committing structural changes.
---

# Architecture Review Skill

## When to Use

- Before merging any pull request that touches multiple domains.
- When adding a new module, service, repository, or domain.
- When refactoring imports or dependency relationships.
- When a code change crosses layer boundaries.

## Workflow

1. **Identify affected layers**: Which layers does this change touch? (Router, Service, Repository, Infrastructure)
2. **Check dependency direction**: Verify arrows only point downward (Router → Service → Repository → ORM).
3. **Verify domain boundaries**: Does the change access another domain's repository directly?
4. **Check for circular imports**: Does module A import B while B imports A?
5. **Validate extension points**: Does the change follow documented extension patterns in `ARCHITECTURE.md`?
6. **Review event bus usage**: Are cross-domain side effects triggered through domain events?
7. **Report violations**: List all constraint violations with file, line, and rule reference.

## Hard Rules (from ARCHITECTURE.md)

| # | Rule |
| :--- | :--- |
| 1 | Router → Service → Repository → ORM/Qdrant. Never skip layers. |
| 2 | No business logic in routers. |
| 3 | No ORM access from routers. |
| 4 | No Qdrant calls from routers. |
| 5 | No embedding creation in routers. |
| 6 | Workers only process queued jobs. |
| 7 | No circular imports. |
| 8 | Services own business logic. |
| 9 | Repositories are data access only. |
| 10 | Unit of Work wraps transactions. |

## Checklist

- [ ] No layer violations detected.
- [ ] Dependency direction is correct (downward only).
- [ ] No circular imports introduced.
- [ ] Domain boundaries respected.
- [ ] Extension points followed.
- [ ] Cross-domain communication uses events.
- [ ] New modules registered in appropriate factories/registries.

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [CODING_STANDARD.md](../../CODING_STANDARD.md)
