---
name: api-review
description: >
  Use when designing or reviewing REST API endpoints: resource naming, HTTP methods,
  status codes, error responses, pagination, filtering, sorting, idempotency,
  versioning, and OpenAPI schema compliance.
---

# API Review Skill

## When to Use

- Designing new API endpoints.
- Reviewing existing endpoint contracts.
- Verifying OpenAPI schema accuracy.
- Adding pagination, filtering, or sorting.

## REST Conventions

### Resource Naming
- Use plural nouns: `/claims`, `/reports`, `/snapshots`.
- Nested resources for relationships: `/claims/{id}/comments`.
- No verbs in URLs. Use HTTP methods for actions.

### HTTP Methods
| Method | Purpose | Idempotent |
| :--- | :--- | :--- |
| `GET` | Read resource(s) | ✅ |
| `POST` | Create resource | ❌ |
| `PUT` | Replace resource | ✅ |
| `PATCH` | Partial update | ❌ |
| `DELETE` | Remove resource | ✅ |

### Status Codes
| Code | When |
| :--- | :--- |
| `200` | Successful read or update |
| `201` | Resource created |
| `204` | Successful delete (no body) |
| `400` | Malformed request |
| `401` | Missing or invalid authentication |
| `403` | Authenticated but insufficient permissions |
| `404` | Resource not found |
| `409` | Conflict (duplicate, state violation) |
| `422` | Validation error (Pydantic) |
| `429` | Rate limited |
| `500` | Unexpected server error |

### Error Response Format
```json
{
  "detail": "Claim not found",
  "code": "ENTITY_NOT_FOUND",
  "request_id": "req_abc123"
}
```

### Pagination
```
GET /claims?page=1&page_size=50

Response:
{
  "items": [...],
  "total": 1234,
  "page": 1,
  "page_size": 50,
  "pages": 25
}
```

## Checklist

- [ ] Resource names are plural nouns.
- [ ] HTTP methods match CRUD semantics.
- [ ] Status codes are correct for each response path.
- [ ] Error responses include `detail` and `request_id`.
- [ ] List endpoints are paginated.
- [ ] OpenAPI schema reflects the endpoint.
- [ ] Request/response models use Pydantic DTOs.

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md) §7 (API Design Principles)
- [CODING_STANDARD.md](../../CODING_STANDARD.md) §3 (Pydantic DTOs)
