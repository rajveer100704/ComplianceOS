# ComplianceOS Security Engineering Rules

> **Scope**: This document defines internal engineering security rules for developers and agents.
> For the public vulnerability reporting policy, see [SECURITY.md](../../SECURITY.md).

---

## 1. Authentication & Token Security

### JWT Rules

- **Sign tokens with RS256** (asymmetric) in production. HS256 is acceptable only in development.
- **Set short expiration**: Access tokens ≤ 15 minutes. Refresh tokens ≤ 7 days.
- **Include minimal claims**: `sub`, `role`, `iat`, `exp`. Never include passwords or PII in JWT payload.
- **Validate all claims on every request**: Verify `exp`, `iss`, `aud`. Reject expired or malformed tokens.
- **Rotate signing keys**: Support key rotation without invalidating all active sessions. Use `kid` header.

### Refresh Token Rules

- **Store refresh tokens hashed** (SHA-256 or bcrypt). Never store plaintext.
- **Implement rotation**: Each refresh grants a new refresh token and invalidates the old one.
- **Detect replay attacks**: If an already-used refresh token is presented, revoke the entire token family.
- **Bind to user agent and IP** (optional): Flag anomalous usage patterns.

### Session Rules

- **Use secure, HttpOnly, SameSite cookies** for session identifiers.
- **Set `SameSite=Lax`** minimum. Use `Strict` where possible.
- **Regenerate session ID** after authentication state changes (login, role change).
- **Implement session timeout**: Inactive sessions expire after 30 minutes.

---

## 2. OAuth2 Security

### State Parameter

- **Always use the `state` parameter** to prevent CSRF attacks on OAuth callbacks.
- **Generate state as a cryptographically random string** (≥ 32 bytes).
- **Verify state on callback**: Reject requests where state doesn't match.

### PKCE (Proof Key for Code Exchange)

- **Use PKCE** for all OAuth2 authorization code flows.
- **Generate `code_verifier`** as a cryptographically random string (43–128 characters).
- **Derive `code_challenge`** using S256 method.

### Callback Security

- **Validate redirect URI**: Only accept pre-registered redirect URIs.
- **Exchange authorization code immediately**: Codes are single-use and short-lived.
- **Verify `id_token` signature** from the identity provider.

---

## 3. Secrets Management

### Rules

- **Never hardcode secrets** in source code. Use environment variables or secret managers.
- **Never commit `.env` files** to version control. Use `.env.example` with placeholders.
- **Never log secrets**: API keys, bearer tokens, passwords, OAuth client secrets.
- **Hash API keys with SHA-256** before storing. Compare hashes on authentication.
- **Encrypt sensitive fields at rest**: Use AES-256-GCM for fields like personal identifiers.
- **Use separate secrets per environment**: Development, staging, and production must have different keys.

### Secret Detection

```python
# ❌ NEVER
api_key = "sk-live-abc123def456"
password = "mysecretpassword"

# ✅ ALWAYS
from config.settings import settings
api_key = settings.API_KEY
```

---

## 4. Input Validation & Injection Prevention

### SQL Injection

- **Parameterized queries only.** Never use string interpolation or f-strings in SQL.
  ```python
  # ❌ NEVER
  query = f"SELECT * FROM users WHERE id = '{user_id}'"

  # ✅ ALWAYS (SQLAlchemy)
  result = await session.execute(
      select(User).where(User.id == user_id)
  )
  ```
- **Use SQLAlchemy ORM** exclusively. No raw SQL unless absolutely necessary, and even then, use `text()` with bound parameters.

### XSS Prevention

- **Escape all user-provided content** before rendering in HTML.
- **Set `Content-Type: application/json`** for API responses.
- **Use Content Security Policy headers** via `SecurityHeadersMiddleware`.

### CSRF Protection

- **Validate `Origin` and `Referer` headers** on state-changing requests.
- **Use CSRF tokens** for form-based submissions (if applicable).
- **OAuth state parameter** serves as CSRF protection for OAuth flows.

---

## 5. Rate Limiting

### Rules

- **Rate limit all authentication endpoints**: Login, token refresh, password reset.
- **Stricter limits on auth**: ≤ 10 requests per minute per IP for login attempts.
- **General API rate limit**: Configurable via `settings.RATE_LIMIT_PER_MINUTE` (default: 120).
- **Return `429 Too Many Requests`** with `Retry-After` header when limit is exceeded.
- **Log rate limit violations** for security monitoring.

---

## 6. Security Headers

The following headers must be set on all responses (via `SecurityHeadersMiddleware`):

| Header | Value |
| :--- | :--- |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Content-Security-Policy` | `default-src 'self'` (adjust as needed) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |

---

## 7. CORS Configuration

- **Never use `*` in production.** Specify exact allowed origins.
- **Restrict methods**: Only allow `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.
- **Restrict headers**: Only allow headers your application actually uses.
- **Set `allow_credentials=True`** only if cookies are used for auth.

```python
# Production CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.complianceos.com"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    allow_credentials=True,
)
```

---

## 8. Data Protection & PII

### Rules

- **Minimize PII collection**: Only collect what's necessary.
- **Encrypt PII at rest**: Use field-level encryption for email, names, etc.
- **Never log PII**: Email addresses, names, IP addresses (in production), session tokens.
- **Implement data retention policies**: Auto-delete inactive user data after defined period.
- **Audit trail**: Log who accessed sensitive data (not the data itself).

---

## 9. Dependency Security

- **Pin dependency versions** in `requirements.txt`.
- **Regularly audit dependencies**: `pip audit` or GitHub Dependabot.
- **Never install packages from untrusted sources.**
- **Review new dependencies** before adding: check maintainership, license, known vulnerabilities.

---

## 10. Threat Model (STRIDE)

| Threat | Mitigation |
| :--- | :--- |
| **Spoofing** | OAuth2, JWT verification, API key hashing |
| **Tampering** | RS256 token signing, HMAC webhook signatures |
| **Repudiation** | Immutable audit logs, request ID tracing |
| **Information Disclosure** | Encryption at rest, TLS in transit, no PII in logs |
| **Denial of Service** | Rate limiting, connection pooling, input size limits |
| **Elevation of Privilege** | RBAC enforcement, role hierarchy, principle of least privilege |
