# ComplianceOS Coding Standard

This document defines naming conventions, design patterns, dependency injection rules, error handling, logging, and code organization standards for all ComplianceOS contributors and autonomous agents.

---

## 1. Naming Conventions

| Element | Convention | Example |
| :--- | :--- | :--- |
| Functions / Methods | `snake_case` | `create_review_snapshot()` |
| Variables | `snake_case` | `claim_count` |
| Classes | `PascalCase` | `ReviewService` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS` |
| Modules / Files | `snake_case` | `review_service.py` |
| Pydantic Models | `PascalCase` + suffix | `ClaimCreateRequest`, `ClaimResponse` |
| SQLAlchemy Models | `PascalCase` (singular) | `ComplianceRequest`, `ReviewComment` |
| Repositories | `PascalCase` + `Repository` | `CommentRepository` |
| Services | `PascalCase` + `Service` | `ReviewService` |
| Routers | Module-level, no class | `review_router.py` |
| Test Files | `test_` prefix | `test_review_service.py` |
| Test Functions | `test_` prefix, descriptive | `test_create_snapshot_returns_receipt()` |

### Naming Rules

- **No abbreviations** unless universally understood (`db`, `id`, `url`, `api`, `jwt`, `http`).
- **Boolean variables**: Prefix with `is_`, `has_`, `can_`, `should_` (`is_approved`, `has_evidence`).
- **Collections**: Use plural nouns (`claims`, `snapshots`, `comments`).
- **Private methods**: Single underscore prefix (`_compute_risk_score()`).
- **Constants**: Module-level, uppercase (`DEFAULT_PAGE_SIZE = 50`).

---

## 2. Module & File Organization

### Import Order

```python
# 1. Standard library
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Project modules
from config.settings import settings
from database.session import get_session
from review.services.review_service import ReviewService
```

- One blank line between each group.
- Absolute imports only. No relative imports (`from . import`).
- Never use wildcard imports (`from module import *`).

### File Structure

- **One primary class per file** for models, repositories, and services.
- **Routers** may define multiple endpoints in a single file.
- **Tests** mirror the source structure: `review/services/review_service.py` → `tests/review/services/test_review_service.py`.

---

## 3. Pydantic DTOs

### Request Models

```python
class ClaimCreateRequest(BaseModel):
    """Request body for creating a new compliance claim."""
    text: str = Field(..., min_length=10, max_length=5000, description="Claim text")
    regulation_id: Optional[str] = Field(None, description="Target regulation identifier")
```

### Response Models

```python
class ClaimResponse(BaseModel):
    """API response for a compliance claim."""
    id: str
    text: str
    verdict: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Rules

- **Never expose ORM models directly** in API responses. Always use a Pydantic response model.
- **Request models**: Suffix with `Request` or `Create`/`Update`/`Patch`.
- **Response models**: Suffix with `Response`.
- **Internal DTOs**: Suffix with `DTO` for inter-service data transfer.
- **Validate at the boundary**: All validation happens in Pydantic models, not in services.

---

## 4. Dependency Injection

### FastAPI Depends()

```python
# Router uses Depends() for all injectable dependencies
@router.post("/claims", response_model=ClaimResponse)
async def create_claim(
    request: ClaimCreateRequest,
    session: AsyncSession = Depends(get_session),
    user: Dict[str, Any] = Depends(get_current_user),
):
    service = ReviewService(session)
    return await service.create_claim(request, user)
```

### Rules

- **Every dependency** must be injected via `Depends()`, never constructed manually in router functions.
- **Session lifecycle** is managed by the session factory. Never create sessions manually.
- **Auth injection** uses `get_current_user` dependency. Never parse auth headers manually in routes.
- **Config injection** uses `settings` singleton from `config/settings.py`.

---

## 5. Repository Pattern

### Contract

```python
class CommentRepository:
    """Data access layer for review comments. No business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, comment_id: str) -> Optional[ReviewComment]:
        result = await self.session.execute(
            select(ReviewComment).where(ReviewComment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def create(self, comment: ReviewComment) -> ReviewComment:
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def list_by_claim(self, claim_id: str) -> List[ReviewComment]:
        result = await self.session.execute(
            select(ReviewComment)
            .where(ReviewComment.claim_id == claim_id)
            .order_by(ReviewComment.created_at.desc())
        )
        return list(result.scalars().all())
```

### Rules

- **Repositories are data access only.** No business decisions, no validation, no side effects.
- **One repository per aggregate root** (e.g., `CommentRepository`, `SnapshotRepository`).
- **Return ORM model instances**, not dicts. The service layer converts to DTOs.
- **Use `flush()` not `commit()`**. The Unit of Work manages transaction boundaries.
- **Parameterized queries only.** Never use string interpolation in SQL.

---

## 6. Service Layer

### Contract

```python
class ReviewService:
    """Business logic for the review workflow domain."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.comment_repo = CommentRepository(session)
        self.snapshot_repo = SnapshotRepository(session)

    async def add_comment(
        self, claim_id: str, text: str, user: Dict[str, Any]
    ) -> CommentResponse:
        # Business validation
        claim = await self._get_claim_or_raise(claim_id)

        # Create entity
        comment = ReviewComment(
            id=str(uuid.uuid4()),
            claim_id=claim_id,
            text=text,
            author=user["sub"],
            created_at=datetime.now(timezone.utc),
        )

        # Persist via repository
        await self.comment_repo.create(comment)
        await self.session.commit()

        # Return DTO
        return CommentResponse.model_validate(comment)
```

### Rules

- **All business logic lives here.** Validation, authorization checks, domain rules.
- **Services call repositories**, never the other way around.
- **Services raise domain exceptions** (e.g., `ClaimNotFoundError`), not `HTTPException`.
- **Services return DTOs or domain objects**, never raw ORM models to routers.
- **Services manage transaction boundaries** via commit/rollback.

---

## 7. Error Handling

### Exception Hierarchy

```python
# Base domain exception
class ComplianceOSError(Exception):
    """Base exception for all ComplianceOS domain errors."""

class EntityNotFoundError(ComplianceOSError):
    """Raised when a requested entity does not exist."""

class AuthorizationError(ComplianceOSError):
    """Raised when a user lacks permission for an operation."""

class ValidationError(ComplianceOSError):
    """Raised when business validation fails."""
```

### Router Exception Handling

```python
@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(claim_id: str, ...):
    try:
        return await service.get_claim(claim_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Claim not found")
    except AuthorizationError:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
```

### Rules

- **Services raise domain exceptions.** Never raise `HTTPException` from services.
- **Routers catch domain exceptions** and convert to appropriate HTTP responses.
- **Never use bare `except:`**. Always catch specific exceptions.
- **Include context** in exception messages for debugging.

---

## 8. Logging

### Convention

```python
import logging

logger = logging.getLogger(__name__)

# Structured log with context
logger.info("Claim reviewed", extra={
    "claim_id": claim_id,
    "verdict": verdict,
    "reviewer": user["sub"],
    "request_id": request_id,
})
```

### Rules

- **Use `logging.getLogger(__name__)`** for module-specific loggers.
- **Structured JSON output** via `observability/config.py` setup.
- **Never log**: Secrets, API keys, bearer tokens, passwords, PII, full request bodies containing sensitive data.
- **Always log**: Request IDs, operation names, entity IDs, timing metrics, error details.
- **Log levels**:
  - `DEBUG`: Detailed diagnostic information.
  - `INFO`: Normal operational events (request received, claim processed).
  - `WARNING`: Recoverable issues (retry, fallback activated).
  - `ERROR`: Failures that need attention (DB connection lost, external API error).
  - `CRITICAL`: System-level failures (startup failure, data corruption).

---

## 9. Transaction Boundaries

### Unit of Work

```python
from database.transaction import UnitOfWork

async with UnitOfWork(session) as uow:
    repo = CommentRepository(uow.session)
    await repo.create(comment)
    await uow.commit()
```

### Rules

- **Never call `session.commit()` in repositories.** Only services or the Unit of Work commit.
- **One transaction per business operation.** Don't span transactions across multiple HTTP requests.
- **Rollback on exception.** The Unit of Work context manager handles automatic rollback.
- **Use `flush()` in repositories** to get generated IDs without committing.

---

## 10. Async Rules

- **All I/O operations must be async.** No synchronous database calls, HTTP requests, or file reads in async contexts.
- **Use `async def` for all route handlers, service methods, and repository methods.**
- **Use `httpx.AsyncClient`** for outbound HTTP calls. Never use `requests`.
- **Use `aiofiles`** if file I/O is needed in async context.
- **Never use `time.sleep()`.** Use `asyncio.sleep()` in async code.

---

## 11. Configuration

- **All configuration via environment variables** loaded through `config/settings.py`.
- **Never hardcode** connection strings, secrets, API keys, or environment-specific values.
- **Use `.env` for local development.** Never commit `.env` files.
- **Provide `.env.example`** with placeholder values for all required variables.
- **Validate configuration at startup** via `settings.validate_startup()`.
