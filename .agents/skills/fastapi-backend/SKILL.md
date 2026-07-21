---
name: fastapi-backend
description: >
  Use when implementing FastAPI backend features: routes, services, repositories,
  DTOs, dependency injection, middleware, and background tasks. Enforces the
  Router → Service → Repository layering and async-first patterns.
---

# FastAPI Backend Skill

## When to Use

- Implementing new API endpoints.
- Creating or modifying services, repositories, or DTOs.
- Adding middleware or dependency injection.
- Wiring background worker tasks.

## Workflow

1. **Read the API contract** for the feature (`roadmap/v*.*/API.md`).
2. **Create/update ORM models** in `database/models/`.
3. **Create Alembic migration**: `alembic revision --autogenerate -m "description"`.
4. **Create repository** in `<domain>/repositories/` — data access only, no logic.
5. **Create service** in `<domain>/services/` — all business logic here.
6. **Create Pydantic DTOs** — request models (suffix `Request`), response models (suffix `Response`).
7. **Create router** — validate input, inject dependencies, delegate to service, map errors to HTTP.
8. **Register route** in `main.py`.
9. **Write tests** — unit (service), integration (service + repo + DB), API (TestClient).
10. **Update OpenAPI** — verify schema reflects new endpoints.

## Rules

### Router Layer
```python
@router.post("/resource", response_model=ResourceResponse, status_code=201)
async def create_resource(
    request: ResourceCreateRequest,
    session: AsyncSession = Depends(get_session),
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = ResourceService(session)
    try:
        return await service.create(request, user)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
```

- No business logic.
- No direct DB or Qdrant access.
- Use `Depends()` for all injected dependencies.
- Map domain exceptions to `HTTPException`.

### Service Layer
- All business logic and validation.
- Call repositories, never access ORM directly.
- Raise domain exceptions, never `HTTPException`.
- Manage transaction boundaries.

### Repository Layer
- Data access only (CRUD).
- Use `flush()` not `commit()`.
- Parameterized queries only.
- Return ORM model instances.

### DTOs
- Pydantic `BaseModel` for all request/response schemas.
- Never expose ORM models in API responses.
- Validate at the boundary with Pydantic field constraints.

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [CODING_STANDARD.md](../../CODING_STANDARD.md)
- [TESTING.md](../../TESTING.md)
