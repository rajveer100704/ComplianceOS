---
name: release
description: >
  Use when preparing, tagging, and executing a platform release: running quality gates,
  updating release notes, bumping semantic versioning, and creating git tags.
---

# Platform Release Skill

## When to Use

- Executing a release checklist for a version milestone (`v1.0.0`, `v1.1.0`, etc.).
- Running final pre-release quality gates (Black, Ruff, MyPy, pytest, Docker).
- Updating `CHANGELOG.md` and `ROADMAP.md`.
- Tagging and pushing release commits to GitHub.

## Release Workflow Checklist

```
1. Run Formatting Check   → black --check .
2. Run Linter             → ruff check .
3. Run Type Checker       → mypy .
4. Run Full Test Suite    → pytest --cov --cov-report=xml
5. Verify Coverage        → Ensure coverage ≥ 80%
6. Verify Docker Build    → docker build -t complianceos:release .
7. Run Smoke Tests        → Validate /healthz, /readyz, /metrics
8. Update CHANGELOG       → Move [Unreleased] items to [vX.Y.Z]
9. Update ROADMAP         → Mark completed items as [x]
10. Commit & Tag Release  → git tag -a vX.Y.Z -m "Release vX.Y.Z"
11. Push Release          → git push origin main --tags
```

## Semantic Versioning Rules

- **MAJOR (`vX.0.0`)**: Incompatible API changes, major architectural redesigns.
- **MINOR (`v1.X.0`)**: Backwards-compatible new feature additions (OAuth, Multi-tenancy, Integrations).
- **PATCH (`v1.0.X`)**: Backwards-compatible bug fixes and security patches.

## Checklist

- [ ] All automated tests pass cleanly.
- [ ] Code coverage meets or exceeds 80%.
- [ ] Docker container builds successfully.
- [ ] `CHANGELOG.md` contains complete release notes.
- [ ] `ROADMAP.md` status updated.
- [ ] Git tag created and pushed to GitHub.

## References

- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md) §8 (Definition of Done)
