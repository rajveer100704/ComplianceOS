# Product Requirement Document (PRD) — Version 1.1: Authentication & Session Identity

## 1. Problem Statement
ComplianceOS currently uses development bearer tokens (`jwt_role_admin`, `jwt_role_reviewer`) and static API keys. There is no real identity provider, session management, or signed token verification, preventing multi-user deployments.

## 2. Goals
- Support Google OAuth2 as the primary authentication provider.
- Implement production-grade RS256 JWT signing, key rotation, and validation.
- Implement refresh token rotation with single-use enforcement and replay detection.
- Provide session management with secure cookie handling and explicit logout.

## 3. Non-Goals
- Microsoft / GitHub OAuth (deferred to v1.1.1 or v1.2.0).
- Multi-tenant organization boundaries (handled in v1.2.0).

## 4. User Stories
- **As a reviewer**, I can click "Login with Google", authorize via OIDC, and be redirected into the 3-Pane Workstation authenticated.
- **As an admin**, I can access protected admin APIs using my RS256 signed JWT token.
- **As a user**, my session automatically refreshes in the background without forcing me to log in every 15 minutes.

## 5. Acceptance Criteria
- [ ] Successful Google OAuth2 authorization code flow with PKCE and state validation.
- [ ] RS256 JWT access tokens issued (15-minute expiration) containing sub, role, iat, exp.
- [ ] Hashed refresh tokens stored in database with automatic rotation on refresh calls.
- [ ] Replay detection: using an already-used refresh token revokes the entire token family.
- [ ] `GET /auth/me` returns current user profile and role details.
