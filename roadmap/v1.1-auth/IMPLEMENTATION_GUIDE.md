# Implementation Guide — Version 1.1: Authentication & Session Identity

Follow this step-by-step execution plan in exact sequence:

1. **Step 1 — Database Models & Migrations**: Define `User`, `OAuthAccount`, `RefreshToken`, `Session` models in `database/models/` and run `alembic revision --autogenerate -m "add v1.1 auth models"`.
2. **Step 2 — Repositories**: Implement `UserRepository` and `TokenRepository` with async SQLAlchemy selectinload queries.
3. **Step 3 — JWT & Auth Services**: Implement `JWTService` (RS256 signing/verification) and `AuthService` (Google OAuth code exchange, refresh token rotation).
4. **Step 4 — API Routers**: Create `auth/router.py` containing `/login/google`, `/callback/google`, `/token/refresh`, `/logout`, `/me`.
5. **Step 5 — Middleware & Dependency Integration**: Update `auth/dependencies.py` to inject current authenticated user from RS256 JWT tokens.
6. **Step 6 — Workstation UI Integration**: Add Google OAuth login button and avatar user menu to `index.html`.
7. **Step 7 — Automated Verification**: Write unit tests for RS256 signing, integration tests for OAuth callbacks, and API route tests.
