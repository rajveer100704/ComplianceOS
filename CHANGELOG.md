# Changelog

All notable changes to the ComplianceOS platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.5.0] - 2026-07-23

### Added

#### Policy Storage Domain (`policy/`)
- **Immutable Policy Versioning**: `PolicyModel` + `PolicyVersionModel` ORM pair — every policy change creates a new, append-only version with SHA-256 checksum. Active version pointer (`current_version_id`) updated atomically.
- **Policy Rollback**: `PolicyRepository.rollback_version()` restores any prior version by creating a new ACTIVE version, fully preserving lineage and audit trail.
- **System Policy Packs**: `SystemPolicyPackModel` — global immutable compliance framework templates (FAA Part 450, NRC 10 CFR, SOC 2). Organizations install packs via `OrganizationPolicyPackModel`.
- **Policy Dependency Graph**: `PolicyDependencyModel` recording parent→child relationships between policies for cycle detection and DAG-ready ordering.
- **Policy Analytics Snapshots**: `PolicyAnalyticsSnapshotModel` — time-series rollups (`HOURLY` / `DAILY` / `MONTHLY`) tracking `times_executed`, `allow_rate`, `block_rate`, and `avg_latency_ms` without expensive runtime aggregation.
- **Policy Pydantic Schemas**: `policy/schemas.py` — full Pydantic v2 (`ConfigDict`) DTO set covering Create / Response / Simulation payloads.

#### Policy Engine Domain (`policy_engine/`)
- **AST Compiler + LRU Cache**: `PolicyCompiler` tokenises and compiles human-readable condition expressions (`risk_score > 80 AND status == UNSUPPORTED`) into a JSON AST. SHA-256-keyed `CompilerCache` prevents repeated compilation.
- **Policy Validator**: `PolicyValidator` statically validates compiled ASTs before activation, rejecting malformed or incomplete trees.
- **Policy Evaluator**: `PolicyEvaluator` evaluates a compiled AST against a `PolicyContext`, producing a structured `PolicyDecision` object with `allowed`, `matched_rules`, `blocked_rules`, and an `EvaluationTrace` containing per-rule status/value/latency.
- **Policy Simulator**: `PolicySimulator` runs dry-run batch evaluations over historical claim samples, returning per-sample decisions for pre-activation impact analysis.
- **Policy Impact Analyzer**: `PolicyImpactAnalyzer` runs the simulator and computes aggregate metrics (`would_allow`, `would_block`, `would_escalate`, `block_rate`, `escalate_rate`, `avg_latency_ms`).
- **Policy Registry**: `PolicyRegistry` maps `DomainEventCatalog` trigger types to registered evaluator pipelines, enabling event-driven policy dispatch.

#### Workflow Engine Domain (`workflow/`)
- **DAG Workflow Models**: `WorkflowDefinitionModel`, `WorkflowExecutionModel`, `WorkflowStepExecutionModel` — full execution history with step-level latency, retry count, and error messages.
- **Retry Policy Strategies**: `RetryPolicy` enum with `NONE`, `LINEAR`, `EXPONENTIAL`, and `EXPONENTIAL_JITTER` delay calculators.
- **Typed Workflow Context**: `WorkflowContext` strongly-typed context dataclass carrying `organization_id`, `policy_id`, `claim`, `event_type`, and arbitrary metadata through action pipelines.
- **Pluggable Action Interface**: `BaseWorkflowAction` ABC defining `action_key`, `retry_policy`, and async `execute(context)` contract.
- **Action Registry**: `ActionRegistry` maintaining named action plugins, supporting `register`, `get`, `list_registered`.
- **Built-in Action Plugins**: `PDFReportAction`, `StorageUploadAction`, `SlackNotificationAction`, `JiraIssueAction` — production-ready adapters wired to existing v1.3 connectors.
- **DAG Workflow Executor**: `WorkflowExecutor` resolving action dependency order, executing steps with configurable retry/back-off, and recording per-step execution history.

#### Events Domain (`events/`)
- **Domain Event Catalog**: `DomainEventCatalog` centralising all platform event type constants (`claim.approved`, `review.completed`, `policy.violated`, `report.generated`, etc.) as a single source of truth for trigger routing.

#### Admin Domain (`admin/`)
- **Admin REST API**: `GET/POST /api/v1/organizations/{org_id}/admin/policies` — policy CRUD with expression compilation on write.
- **Policy Simulation Endpoint**: `POST /api/v1/organizations/{org_id}/admin/policies/simulate` — dry-run batch evaluation returning `total_evaluated`, `allowed_count`, `blocked_count`, `escalated_count`.
- **Audit Log Endpoints**: `GET /api/v1/organizations/{org_id}/admin/audit-logs` (filtered query) and `GET .../audit-logs/export?format=csv` (streaming CSV export).
- **Worker Queue Status**: `GET /api/v1/organizations/{org_id}/admin/workers/queue` — worker health and queue depth dashboard endpoint.

#### Audit Domain (`audit/`)
- **Platform-Wide Audit Service**: `AuditService` recording immutable `AuditLogModel` entries for every governance action with actor, resource, event type, and JSON diff payload.

#### Generic State Machine (`review/state_machine.py`)
- **Reusable State Machine**: `StateMachine` generic class enforcing valid transitions, raising `InvalidTransitionError` on illegal state changes. Consumed by workflow executor and review workflows.

#### Alembic Migration
- `c5f1a3b7d9e4_add_v1_5_policy_workflow_tables.py` — creates 9 new tables: `system_policy_packs`, `organization_policy_packs`, `policies`, `policy_versions`, `policy_rules`, `policy_dependencies`, `policy_analytics_snapshots`, `workflow_definitions`, `workflow_executions`, `workflow_step_executions`.

#### Test Suite
- **Policy Engine Unit Tests** (`tests/policy/test_policy_engine.py`): Compiler + cache, validator, evaluator pass/fail — 4 cases.
- **Workflow Engine Unit Tests** (`tests/workflow/test_workflow_engine.py`): Live run and dry-run executor — 2 cases.
- **Admin API Integration Tests** (`tests/admin/test_admin_router.py`): Policy CRUD, simulation, audit log query/export, worker queue — 1 integration test covering 5 endpoints.
- **Audit Service Unit Tests** (`tests/audit/test_audit_service.py`): Append and query audit log entries.
- **Total platform tests passing: 167/167.**

### Changed
- **`database/models/__init__.py`**: Registered all 10 v1.5 ORM models with `Base.metadata` so `create_all` correctly provisions policy/workflow tables in the test fixture in-memory SQLite database.
- **`main.py`**: Mounted `admin_router` and `policy_router` under `/api/v1/organizations/{org_id}/admin`.
- **`roadmap/v1.5-policy-engine/ADR.md`**: Finalized architectural decisions for immutable versioning, AST compiler, policy simulator, DAG workflow engine, and centralized event catalog.

### Fixed
- **Test Isolation** (`tests/admin/test_admin_router.py`): Migrated from persistent `compliance.db` session to isolated in-memory `db_session` fixture + `dependency_overrides`, eliminating `UNIQUE constraint failed` failures on repeated runs.
- **Pydantic v2 Deprecations** (`policy/schemas.py`): Replaced 4 class-based `Config` inner classes with `model_config = ConfigDict(from_attributes=True)`.
- **Timezone-Aware Datetimes**: Replaced all `datetime.utcnow()` calls in `policy/repository.py`, `policy/models.py`, and `workflow/models.py` with `datetime.now(UTC)` — resolves Python 3.12+ `DeprecationWarning`.

---



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
