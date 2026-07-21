---
name: testing
description: >
  Use when writing or reviewing tests: unit tests, integration tests, API tests,
  repository tests, regression tests, performance benchmarks. Enforces test pyramid,
  coverage thresholds, fixture conventions, and mocking boundaries.
---

# Testing Skill

## When to Use

- Writing tests for any new feature or bug fix.
- Reviewing test coverage and quality.
- Setting up test fixtures or factories.
- Deciding what to mock and what to test with real dependencies.

## Every Feature Must Include

| Test Type | Required | Scope |
| :--- | :--- | :--- |
| Unit Tests | ✅ | Service methods, utility functions |
| Repository Tests | ✅ | Data access against SQLite |
| API Tests | ✅ (if endpoints) | HTTP request/response via TestClient |
| Integration Tests | ✅ | Service → Repository → DB flow |
| Regression Tests | ✅ (if bug fix) | Reproduce bug, verify fix |
| Performance Tests | ⚠️ Recommended | Benchmark critical paths |

## Mocking Rules

- **Mock at the boundary**: External APIs, Qdrant, file system, time.
- **Never mock the system under test.**
- **Never mock internal services** when testing the layer above.
- **Use `AsyncMock`** for async methods.
- **Prefer dependency injection** over `@patch`.

## Coverage

- Line coverage ≥ 80% (CI blocking).
- New code coverage ≥ 90% (PR review).

## References

- [TESTING.md](../../TESTING.md)
