---
name: feature-development
description: >
  Use when implementing any feature end-to-end: guides the sequential workflow
  from reading PRD/ADR contracts through backend/frontend implementation, testing,
  documentation updates, and conventional commits.
---

# Feature Development Skill

## When to Use

- Starting implementation of any new feature or roadmap milestone.
- Orchestrating multi-step work across database, backend services, API routers, frontend UI, and test suites.

## Standard Feature Lifecycle

```
1. Read PRD           → Read roadmap/v*.*/PRD.md (goals, criteria)
2. Read ADR           → Read roadmap/v*.*/ADR.md (architecture rationale)
3. Read API Contract  → Read roadmap/v*.*/API.md (endpoint schemas)
4. Read DB Design     → Read roadmap/v*.*/DATABASE.md (models, migrations)
5. Read Architecture  → Read ARCHITECTURE.md (layer constraints)
6. Plan               → Create implementation plan and checklist
7. Implement          → Database → Backend Repositories/Services → Routers → Frontend UI
8. Run Tests          → pytest --cov (verify coverage ≥ 80%)
9. Run Quality Gates  → black + ruff + mypy
10. Self-Review       → Verify against ARCHITECTURE.md constraints
11. Update Docs       → README.md, CHANGELOG.md, API docs
12. Commit & Push     → Conventional commit message, git push
```

## Quality Checklist

- [ ] Feature implemented matching exact API contract specifications.
- [ ] No business logic in routers or repositories.
- [ ] Async-first conventions followed.
- [ ] Unit, integration, and API tests written and passing.
- [ ] Coverage threshold ≥ 80% maintained.
- [ ] Black formatting and Ruff linting pass cleanly.
- [ ] Documentation updated to reflect changes.
- [ ] Conventional commit message used.

## References

- [AGENTS.md](../../AGENTS.md) §10
- [fastapi-backend](../fastapi-backend/SKILL.md)
- [testing](../testing/SKILL.md)
