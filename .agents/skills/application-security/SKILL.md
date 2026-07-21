---
name: application-security
description: >
  Use for general application security: OWASP Top 10, XSS prevention, CSRF protection,
  SQL injection prevention, secrets management, rate limiting, security headers,
  CORS configuration, PII handling, and dependency auditing.
---

# Application Security Skill

## When to Use

- Reviewing code for security vulnerabilities.
- Implementing input validation and sanitization.
- Configuring security headers and CORS.
- Managing secrets and sensitive data.
- Implementing rate limiting.
- Auditing dependencies for known vulnerabilities.

## OWASP Top 10 Checklist

| # | Vulnerability | ComplianceOS Mitigation |
| :--- | :--- | :--- |
| A01 | Broken Access Control | RBAC via `require_role()`, `get_current_user` dependency |
| A02 | Cryptographic Failures | RS256 JWT, SHA-256 hashing, AES-256-GCM encryption |
| A03 | Injection | SQLAlchemy ORM (parameterized), no raw SQL |
| A04 | Insecure Design | Architecture review skill, layered architecture |
| A05 | Security Misconfiguration | `settings.validate_startup()`, security headers middleware |
| A06 | Vulnerable Components | `pip audit`, Dependabot, pinned versions |
| A07 | Auth Failures | OAuth2 + PKCE, refresh rotation, replay detection |
| A08 | Data Integrity Failures | Signed JWTs, immutable audit logs, outbox pattern |
| A09 | Logging Failures | Structured JSON logs, request ID tracing, never log secrets |
| A10 | SSRF | Allowlisted external URLs, no user-controlled redirects |

## Rules

### Input Validation
- Validate all input at the API boundary using Pydantic models.
- Set `max_length` on all string fields.
- Set `ge`/`le` constraints on numeric fields.
- Reject unexpected fields (`model_config = ConfigDict(extra="forbid")`).

### SQL Injection Prevention
- Use SQLAlchemy ORM exclusively.
- If raw SQL is unavoidable, use `text()` with bound parameters.
- Never use f-strings or string concatenation in queries.

### XSS Prevention
- Set `Content-Type: application/json` for all API responses.
- Escape user content before HTML rendering.
- Content Security Policy headers via middleware.

### Secrets Management
- All secrets via environment variables (`config/settings.py`).
- Never commit `.env` files.
- Hash API keys (SHA-256) before storage.
- Encrypt sensitive fields (AES-256-GCM) at rest.
- Rotate secrets on schedule.

### Rate Limiting
- Auth endpoints: ≤ 10 requests/min/IP.
- General API: configurable via `RATE_LIMIT_PER_MINUTE`.
- Return `429` with `Retry-After` header.

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

## References

- [docs/security/SECURITY_ENGINEERING.md](../../docs/security/SECURITY_ENGINEERING.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
