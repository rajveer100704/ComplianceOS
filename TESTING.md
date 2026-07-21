# ComplianceOS Testing Standard

This document defines the test pyramid, coverage thresholds, fixture conventions, mocking rules, and quality gates for all ComplianceOS test suites.

---

## 1. Test Pyramid

```
                    ┌─────────┐
                    │  E2E    │   Few, slow, high confidence
                    │  Tests  │   Browser-based UI flows
                    ├─────────┤
                    │   API   │   Medium count, medium speed
                    │  Tests  │   HTTP endpoint verification
                    ├─────────┤
                    │ Integr. │   Many, moderate speed
                    │  Tests  │   Service + repository + DB
                    ├─────────┤
                    │  Unit   │   Most, fastest
                    │  Tests  │   Isolated logic verification
                    └─────────┘
```

### Distribution Target

| Level | Count | Speed | Isolation |
| :--- | :--- | :--- | :--- |
| **Unit** | ~60% of all tests | < 100ms each | Full isolation, no I/O |
| **Integration** | ~25% of all tests | < 2s each | Real DB (SQLite), mocked externals |
| **API** | ~10% of all tests | < 3s each | Full FastAPI TestClient |
| **E2E** | ~5% of all tests | < 30s each | Browser or HTTP-based full flow |

---

## 2. Coverage Requirements

| Metric | Threshold | Enforcement |
| :--- | :--- | :--- |
| **Line Coverage** | ≥ 80% | CI blocking |
| **Branch Coverage** | ≥ 70% | Advisory |
| **New Code Coverage** | ≥ 90% | PR review |

### Generating Coverage Reports

```bash
pytest --cov=. --cov-report=xml --cov-report=term-missing
```

### Excluded from Coverage

- `database/migrations/` (auto-generated Alembic scripts)
- `__pycache__/`
- Test files themselves
- `config/settings.py` (environment-dependent)

---

## 3. Feature Test Requirements

Every feature must include:

| Test Type | Required | What It Covers |
| :--- | :--- | :--- |
| **Unit Tests** | ✅ Yes | Service methods, utility functions, domain logic |
| **Repository Tests** | ✅ Yes | Data access operations against SQLite |
| **API Tests** | ✅ Yes (if endpoints change) | HTTP request/response contracts |
| **Integration Tests** | ✅ Yes | Multi-layer flows (service → repo → DB) |
| **Regression Tests** | ✅ Yes (if fixing a bug) | Reproduce the bug, then verify the fix |
| **Performance Tests** | ⚠️ Recommended | Benchmark critical paths (retrieval, parsing) |
| **Smoke Tests** | ⚠️ Recommended (for releases) | `/healthz`, `/readyz`, basic CRUD |

**No feature is complete without passing tests.**

---

## 4. File & Naming Conventions

### Test File Naming

```
tests/
├── unit/
│   ├── review/
│   │   ├── test_review_service.py
│   │   └── test_comment_repository.py
│   ├── retrieval/
│   │   └── test_dense_retriever.py
│   └── auth/
│       └── test_jwt_provider.py
├── integration/
│   ├── test_claim_review_flow.py
│   └── test_snapshot_lifecycle.py
├── api/
│   ├── test_claims_api.py
│   └── test_auth_api.py
└── conftest.py
```

### Test Function Naming

```python
# Pattern: test_<action>_<expected_outcome>
def test_create_comment_returns_comment_response():
    ...

def test_create_comment_raises_when_claim_not_found():
    ...

def test_refresh_token_rotation_invalidates_old_token():
    ...

# For parameterized tests
@pytest.mark.parametrize("role,expected", [
    ("Admin", True),
    ("Reviewer", False),
])
def test_require_admin_role_enforcement(role, expected):
    ...
```

---

## 5. Fixture Conventions

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py

@pytest.fixture
async def db_session():
    """Provides a clean async database session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()

@pytest.fixture
def test_client(db_session):
    """Provides a FastAPI TestClient with dependency overrides."""
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user():
    """Returns an admin user context dict."""
    return {"sub": "test_admin", "role": "Admin", "provider": "test"}

@pytest.fixture
def reviewer_user():
    """Returns a reviewer user context dict."""
    return {"sub": "test_reviewer", "role": "Reviewer", "provider": "test"}
```

### Rules

- **Fixtures are scoped appropriately**: `function` (default), `module`, `session`.
- **No global state** between tests. Each test gets a fresh database.
- **Factory fixtures** for creating test entities with sensible defaults.
- **Named clearly**: `db_session`, `test_client`, `admin_user`, `sample_claim`.

---

## 6. Mocking Rules

### Mock at the Boundary

```python
# ✅ CORRECT: Mock the external dependency
@patch("retrieval.stores.qdrant.QdrantClient")
async def test_index_document(mock_qdrant):
    mock_qdrant.upsert.return_value = None
    service = IndexingService(mock_qdrant)
    await service.index(document)

# ❌ WRONG: Mock internal service methods
@patch("review.services.review_service.ReviewService.add_comment")
async def test_add_comment(mock_add):
    ...  # This tests nothing meaningful
```

### Rules

- **Mock external boundaries**: Database, Qdrant, HTTP clients, file system, time.
- **Never mock internal services** when testing the layer above. Use real service instances.
- **Never mock the system under test.** If you're testing `ReviewService`, don't mock `ReviewService`.
- **Use `AsyncMock`** for async methods.
- **Prefer dependency injection** over `@patch` when possible.

---

## 7. Async Test Conventions

```python
import pytest

@pytest.mark.asyncio
async def test_create_snapshot_persists_to_database(db_session):
    service = SnapshotService(db_session)
    receipt = await service.create_snapshot(request_id=1)
    assert receipt.snapshot_id is not None
```

### Rules

- **Use `@pytest.mark.asyncio`** for all async test functions.
- **Use `pytest-asyncio`** plugin.
- **Never use `asyncio.run()` inside tests.** Let pytest-asyncio manage the event loop.

---

## 8. Test Data

### Factories

```python
def make_claim(
    text: str = "The vehicle satisfies flight safety requirements.",
    verdict: str = "SUPPORTED",
    confidence: float = 0.95,
    **overrides,
) -> dict:
    """Factory for claim test data with sensible defaults."""
    data = {
        "id": str(uuid.uuid4()),
        "text": text,
        "verdict": verdict,
        "confidence": confidence,
        "created_at": datetime.now(timezone.utc),
    }
    data.update(overrides)
    return data
```

### Rules

- **Use factory functions** with defaults. Override only the fields relevant to the test.
- **Never use production data** in tests.
- **Keep test data minimal.** Only include fields the test actually exercises.
- **Use deterministic data** (avoid `random` unless testing randomness).

---

## 9. Performance Testing

```python
def test_retrieval_latency(benchmark):
    """Verify retrieval completes within acceptable latency."""
    result = benchmark(retriever.search, query="flight safety", top_k=5)
    assert len(result) == 5

def test_bulk_indexing_throughput(benchmark):
    """Verify bulk indexing meets throughput requirements."""
    documents = [make_document() for _ in range(100)]
    benchmark(indexer.bulk_index, documents)
```

### Performance Targets

| Operation | P95 Target |
| :--- | :--- |
| Single claim retrieval | < 200ms |
| PDF parsing (50 pages) | < 5s |
| Snapshot creation | < 500ms |
| Report generation | < 3s |

---

## 10. Pre-Commit Test Checklist

Before every commit:

```bash
# 1. Run full test suite
pytest --cov --cov-report=term-missing

# 2. Check formatting
black --check .

# 3. Lint
ruff check .

# 4. Type check
mypy .

# 5. Docker build (before release)
docker build -t complianceos:test .
```
