# Implementation Checklist — Version 1.1: Authentication & Session Identity

- [ ] **Backend**
  - [ ] Add `User`, `OAuthAccount`, `RefreshToken`, `Session` models.
  - [ ] Generate and test Alembic migration script.
  - [ ] Implement `UserRepository` and `TokenRepository`.
  - [ ] Implement RS256 `JWTService` with key loading from `settings`.
  - [ ] Implement `GoogleOAuthProvider` and `AuthService`.
  - [ ] Implement `auth/router.py` endpoints.
  - [ ] Update `auth/dependencies.py` for real JWT verification.

- [ ] **Frontend**
  - [ ] Add "Login with Google" button to login page.
  - [ ] Implement `/auth/callback` token parser and local storage sync.
  - [ ] Add auto-refresh interceptor for expired 15-minute access tokens.
  - [ ] Add user profile menu and logout button in navigation topbar.

- [ ] **Tests & Docs**
  - [ ] Unit tests for RS256 token verification and expiry.
  - [ ] Integration tests for refresh token rotation and replay revocation.
  - [ ] API tests for `/auth/login/google` and `/auth/me`.
  - [ ] Update `README.md` and `docs/security/SECURITY_ENGINEERING.md`.
