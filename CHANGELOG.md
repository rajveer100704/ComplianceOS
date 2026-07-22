# Changelog

All notable changes to the ComplianceOS platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.1.0] - 2026-07-22

### Added
- **OAuth Provider Abstraction**: `OAuthProvider` base class and `GoogleOAuthProvider` implementation in `auth/providers/`.
- **RS256 JWT Infrastructure & JWKS**: Asymmetric RS256 token signing, dynamic key loading, key rotation support, and RFC 7517 `GET /.well-known/jwks.json` endpoint with HTTP caching headers (`Cache-Control`, `ETag`).
- **Refresh Token Rotation & Replay Protection**: Single-use refresh tokens stored as HMAC-SHA256 hashes with server pepper, automatic token family revocation upon replay detection, and configurable grace period for concurrent requests.
- **Session Lifecycle & Device Tracking**: Adaptive session state management (`VALID`, `EXPIRED`, `REVOKED`, `HIGH_RISK`), user-agent parsing (browser, OS, device type), heartbeat activity throttling, and 3-way logouts (`current`, `others`, `all`).
- **Permission-First Authorization**: Domain permission enums (`claims:read`, `reports:approve`, `users:manage`), role permission mappings, wildcard permission matching (`*`, `domain:*`), and `SecurityContext` dependency injection.
- **Public Authentication APIs**:
  - `GET /api/v1/auth/google/login`: Initiates OAuth2 login flow with CSRF state parameter.
  - `GET /api/v1/auth/google/callback`: Code exchange, user provisioning, session creation, and HttpOnly cookie issuance (`access_token` Path=/, `refresh_token` Path=/).
  - `POST /api/v1/auth/refresh`: Token rotation via HttpOnly cookie, JSON request body, or Authorization header.
  - `POST /api/v1/auth/logout`: Revokes session and clears cookies across scopes.
  - `GET /api/v1/auth/me`: Returns comprehensive authenticated user profile with active permissions and session metadata.
- **Domain Outbox Events**: Events published for `LoginStarted`, `OAuthCallbackSucceeded`, `SessionCreated`, `RefreshRotated`, `RefreshTokenReplayDetected`, `LogoutCurrent`, `LogoutOthers`, `LogoutAll`, `SessionTouched`, `SessionRevoked`, `AllSessionsRevoked`, `ProfileViewed`.
- **Comprehensive Unit & Integration Test Suite**: 54 test cases covering models, repositories, JWT cryptography, token rotation, sessions, dependencies, and API router endpoints with 82% overall test coverage.

---

## [v1.0.0] - 2026-07-18

### Added
- Initial public release of ComplianceOS platform.
- Dense (Qdrant) + Lexical (BM25) hybrid vector retrieval engine.
- Async SQLAlchemy ORM models, Alembic migrations, and transactional Unit of Work.
- Document parsing pipeline (PyMuPDF + OCR fallback).
- Outbox pattern and background worker task dispatcher.
- 3-Pane Human Review Workstation SPA (`index.html`).
- Versioned review snapshots and semantic diff comparison.
- Report Studio with HTML, Markdown, and JSON exporters.
