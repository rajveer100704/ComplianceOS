---
name: oauth
description: >
  Use when implementing authentication: OAuth2 flows, JWT signing/verification,
  refresh token rotation, session management, login/logout endpoints, and
  user profile retrieval. Covers Google OAuth2, GitHub OAuth, and OIDC.
---

# OAuth & Authentication Skill

## When to Use

- Implementing OAuth2 login flows (Google, GitHub, Microsoft).
- Adding JWT token signing, verification, or rotation.
- Implementing refresh token lifecycle.
- Creating session management.
- Adding login/logout endpoints.
- Implementing user profile retrieval.

## OAuth2 Authorization Code Flow

```
User clicks "Login with Google"
       │
       ▼
GET /auth/login/google
       │
       ├── Generate state (CSRF protection)
       ├── Generate code_verifier + code_challenge (PKCE)
       ├── Store state + code_verifier in session/cookie
       │
       ▼
Redirect to Google Consent Screen
       │
       ▼
User authorizes → Google redirects to callback
       │
       ▼
GET /auth/callback/google?code=...&state=...
       │
       ├── Verify state matches
       ├── Exchange code for tokens (with code_verifier)
       ├── Verify id_token signature
       ├── Extract user info (email, name, picture)
       ├── Lookup or create User
       ├── Create OAuthAccount link
       ├── Issue JWT access token (RS256, 15min)
       ├── Issue refresh token (SHA-256 hashed, 7 days)
       ├── Create Session record
       │
       ▼
Redirect to app with tokens (secure cookie or response body)
```

## Token Lifecycle

```
Access Token (JWT, RS256)
├── Expiry: 15 minutes
├── Claims: sub, role, iat, exp, iss, aud
├── Signed with private key
└── Verified with public key

Refresh Token
├── Expiry: 7 days
├── Stored: SHA-256 hash in database
├── Rotation: New refresh token on each use
├── Replay detection: Reuse invalidates entire family
└── Bound to: user_id, device/user_agent (optional)
```

## Implementation Steps

### Backend

1. **User model** — `database/models/user.py`
2. **OAuthAccount model** — `database/models/oauth_account.py`
3. **RefreshToken model** — `database/models/refresh_token.py`
4. **Session model** — `database/models/session.py`
5. **Alembic migration** — `alembic revision --autogenerate -m "add auth tables"`
6. **User repository** — `auth/repositories/user.py`
7. **Token repository** — `auth/repositories/token.py`
8. **Auth service** — `auth/services/auth_service.py`
9. **JWT service** — `auth/services/jwt_service.py`
10. **OAuth provider (Google)** — `auth/providers/google.py`
11. **Auth router** — `auth/router.py`
12. **Update middleware** — RS256 JWT verification
13. **Update dependencies** — `get_current_user` with real JWT validation
14. **Settings** — Add OAuth config to `config/settings.py`

### Frontend

15. **Login page** — `/auth/login`
16. **Callback handler** — `/auth/callback`
17. **Session provider** — Store tokens, auto-refresh
18. **Protected routes** — Redirect unauthenticated users
19. **User avatar & logout** — Header component

### Tests

20. **Unit tests** — JWT signing/verification, token rotation, role guards
21. **Integration tests** — OAuth callback flow (mocked provider), refresh rotation
22. **API tests** — All auth endpoints

## Failure Modes

| Failure | Mitigation |
| :--- | :--- |
| State mismatch on callback | Reject request, log attempt |
| Expired authorization code | Return 400, prompt re-login |
| Refresh token replay | Revoke entire token family |
| Clock skew on JWT expiry | Allow 30-second leeway |
| Google API unavailable | Return 502, retry with backoff |
| Invalid id_token signature | Reject, do not create session |

## References

- [docs/security/SECURITY_ENGINEERING.md](../../docs/security/SECURITY_ENGINEERING.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
