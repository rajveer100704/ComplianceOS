# Changelog

All notable changes to the ComplianceOS platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.4.0] - 2026-07-23

### Added
- **Unified Observability Architecture**: Architectural five-pillar framework (`Logging`, `Metrics`, `Tracing`, `Health`, `Alerting`) encapsulated by the `ObservabilityService` facade.
- **Correlation-Rich Structured JSON Logging**: `JSONLogFormatter` in `observability/logging.py` automatically parsing and injecting distributed context (`trace_id`, `span_id`, `request_id`, `organization_id`, `user_id`, `session_id`, `endpoint`, `method`, `status_code`, `latency_ms`).
- **OpenTelemetry Distributed Tracing**: OpenTelemetry SDK initialization (`observability/tracing.py`) supporting OTLP exporters, FastAPI auto-instrumentation, and `@trace_span(name)` decorator.
- **Prometheus Metrics Engine & Catalog**: Decoupled `MetricsService` facade (`observability/metrics.py`) providing system performance counters, latency histograms, active request gauges, vector search durations, worker task queues, and Prometheus exposition (`GET /metrics`).
- **Sentry Error Tracking & Scope Correlation**: `setup_sentry` and `set_sentry_context` helper in `observability/sentry.py` injecting tenant, request, and user tags into error tracebacks.
- **Modular Health Diagnostic Framework**: Extensible `BaseHealthChecker` abstract base class and 5 specialized checkers (`DatabaseChecker`, `QdrantChecker`, `WorkerChecker`, `StorageChecker`, `IntegrationChecker`) exposing `/healthz` (liveness), `/readyz` (readiness), and `/health/dependencies` diagnostics endpoints.
- **Observability Middleware**: `ObservabilityMiddleware` in `observability/service.py` timing HTTP request durations, recording Prometheus metrics, setting OpenTelemetry span attributes, and propagating request context headers.
- **Production Monitoring Stack & Dashboards**: Docker Compose stack expanded with Jaeger, Prometheus, Grafana, Loki, Promtail, alongside pre-configured Grafana dashboard JSON definitions (`grafana_api_performance.json`, `grafana_retrieval_pipeline.json`, `grafana_worker_health.json`) and runbooks in `docs/observability/`.
- **Observability Test Suite**: 8 unit & integration test suites (`tests/observability/`) validating facade lifecycle, JSON log correlation, Prometheus exposition, trace propagation, Sentry scopes, and health aggregation probes. Total platform test suite passing: 111/111.

---

## [v1.3.0] - 2026-07-22

### Added
- **Enterprise Business Connectors**: Standardized adapters (`SlackAdapter`, `TeamsAdapter`, `GitHubAdapter`, `JiraAdapter`) for notifications and automated issue creation.
- **Provider Capabilities Engine**: Capabilities catalog (`ProviderCapabilities`) allowing dynamic event matching (`supports(event)`) without hardcoded provider branching.
- **Credential AES-256-GCM Encryption**: `CredentialService` Fernet symmetric encryption and secret rotation (`POST /rotate-secret`) with version tracking (`credential_version`, `rotated_at`).
- **Separated Runtime State & Operational Visibility**: `IntegrationRuntimeStateModel` tracking `health_status`, `consecutive_failures`, `last_success_at`, `last_failure_at`, `next_retry_at`, and `last_probe_duration_ms`.
- **Integration Health Check Service**: `IntegrationHealthCheckService` performing automated probes (`POST /test`, `GET /health`) and updating health status metrics.
- **Parallel Outbox Event Dispatcher**: `EventDispatcher` firing outbox events across active tenant integrations concurrently using `asyncio.gather(..., return_exceptions=True)` with SHA-256 idempotency key deduplication.
- **Resilience Infrastructure**: `CircuitBreaker` state machine managing provider failure states (CLOSED, OPEN, HALF_OPEN) to prevent cascading outages.
- **Object Storage Subsystem (`storage/`)**: Decoupled S3 and Cloudflare R2 object storage providers (`S3StorageProvider`, `R2StorageProvider`, `StorageService`) with presigned upload/download REST endpoints (`/api/v1/organizations/{org_id}/storage/presigned-upload`, `/presigned-download`).
- **Integrations REST API**: Endpoints for creating (`POST`), listing (`GET`), updating (`PATCH`), deleting (`DELETE`), health probing (`GET /health`), testing connection (`POST /test`), and credential rotation (`POST /rotate-secret`).
- **Alembic Migration**: `b4e2f6a8c0d2_add_v1_3_integrations_tables.py` creating `integrations`, `integration_runtime_states`, and `integration_delivery_logs` tables.
- **Automated Test Suite**: 22 unit & integration test cases (`test_adapters.py`, `test_adapter_registry.py`, `test_credential_service.py`, `test_event_dispatcher.py`, `test_integration_models.py`, `test_integration_router.py`, `test_storage_providers.py`) validating connectors, outbox routing, encryption, API contracts, and presigned S3/R2 storage URLs. Total platform tests passing: 103/103.

---

## [v1.2.0] - 2026-07-22

### Added
- **Multi-Tenant SaaS Models**: New ORM models (`Organization`, `OrganizationMembership`, `Team`, `Invitation`) and enums (`MembershipRole`, `InvitationStatus`, `OrganizationPlan`).
- **Organization & Team Domain Package**: `organizations/` package containing business service (`OrganizationService`), outbox events (`events.py`), DTO schemas (`schemas.py`), and API router (`router.py`).
- **Tenant Middleware**: `TenantMiddleware` extracting and attaching active organization ID (`X-Organization-Id` header, `org_id` cookie) to request state.
- **Tenant-Scoped Data Access**: Scoped repositories (`OrganizationRepository`, `OrganizationMembershipRepository`, `InvitationRepository`) with tenant boundaries and soft delete support.
- **Single-Use Invitation Workflow**: Secure single-use token invitations hashed with SHA-256 (`InvitationRepository`, `OrganizationService.invite_member`, `OrganizationService.accept_invitation`).
- **Organization API Endpoints**:
  - `POST /api/v1/organizations`: Creates workspace and assigns creator as OWNER.
  - `GET /api/v1/organizations/me`: Lists organizations for the authenticated user with membership roles.
  - `POST /api/v1/organizations/{org_id}/invitations`: Invites new member with role assignment (`Owner` or `Admin` authorization).
  - `GET /api/v1/organizations/{org_id}/members`: Lists active organization members.
- **Tenant Isolation Test Suite**: 27 unit & integration tests (`test_org_models.py`, `test_org_repositories.py`, `test_tenant_isolation.py`) covering tenant isolation (403), deleted orgs, suspended memberships, invitation replay (410), duplicate invites (409), and default org resolution.

### Changed
- **User Role Migration**: Deprecated and dropped `users.role` and `users.organization_id` columns; membership role (`OrganizationMembership.role`) is now the single source of truth for authorization.
- **SecurityContext Extension**: Injected active `membership` (`OrganizationMembership`) and `organization` (`Organization`) into `SecurityContext`.
- **Alembic Migration**: `a3f1c2d4e5b6_add_v1_2_multitenant_tables.py` creating multi-tenant schema and auto-provisioning a personal organization + OWNER membership for every existing user.

### Fixed
- **Last Owner Removal Protection**: Added `count_owners()` check in `OrganizationMembershipRepository` to prevent removing or downgrading the last organization owner.
- **Deterministic Tenant Resolution**: Enforced multi-tenant context resolution order (`X-Organization-Id` header → `org_id` cookie → default membership by creation timestamp).
- **Invitation Replay Hardening**: Rejection of accepted/expired invitation token replay attempts with explicit HTTP status codes (`410 GONE` / `409 CONFLICT`).

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

### Fixed
- **SQLite Migration Compatibility**: Ensured Alembic migration scripts and test runners handle SQLite type constraints gracefully in local and CI environments.
- **Development Key Fallback**: Added 4-tier key loading strategy with automatic ephemeral in-memory 2048-bit RSA keypair fallback for CI and headless testing.
- **CI Dependency Resolution**: Resolved `PyJWT[crypto]` and `cryptography` dependency requirements in test execution workflows.
- **Circular Import Elimination**: Decoupled `SecurityContext` into `auth/schemas.py` to prevent cyclic initialization dependencies between services and auth dependencies.

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
