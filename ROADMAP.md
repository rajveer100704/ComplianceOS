# ComplianceOS Platform Roadmap

The ComplianceOS development lifecycle follows Semantic Versioning (`v1.0.0` → `v2.0.0`), expanding from a core RAG & compliance review engine into a multi-tenant enterprise compliance platform.

Each version is backed by a self-contained engineering implementation package in `roadmap/v*.*/` containing PRD, ADR, API, DATABASE, IMPLEMENTATION_GUIDE, IMPLEMENTATION_CHECKLIST, RISKS, DECISIONS, and TEST_PLAN contracts.

---

## 🎯 v1.0.0 — Initial Public Release (Completed) ✅
- [x] **Dense & Lexical Hybrid Vector Retrieval**: Qdrant integration with SentenceTransformers & lexical overlap scoring.
- [x] **Async Persistence & Unit of Work**: Async SQLAlchemy ORM models, Alembic migrations, and transactional Unit of Work pattern.
- [x] **Outbox Pattern & Background Workers**: Asynchronous task queue runner for document parsing and report exports.
- [x] **3-Pane Human Review Workstation UI**: Interactive workstation for claim review, decision recording, evidence pinning, and comments.
- [x] **Versioned Snapshots & Semantic Diffing**: Immutable review snapshots with lineage tracking and semantic diff comparison.
- [x] **Compliance Report Studio & Exporters**: Pluggable HTML, Markdown, and JSON exporters with risk matrix visualizer.
- [x] **Production Hardening & Operations**: Pluggable auth, `X-Request-ID` request tracing, `/healthz`/`/readyz`/`/metrics` probes, and Docker Compose stack.

---

## 🔐 v1.1.0 — Authentication & Session Identity (Completed) ✅
> 📦 **Specification Package**: [`roadmap/v1.1-auth/`](roadmap/v1.1-auth/)
- [x] **Google OAuth2 Integration**: Primary OAuth2 authentication provider with provider abstraction (`OAuthProvider`).
- [x] **Production RS256 JWT Security**: Signed RS256 JWT token verification, dynamic JWKS key set (`/.well-known/jwks.json`), and key rotation.
- [x] **Session & Token Management**: Single-use refresh token rotation with replay detection, secure HttpOnly cookies, 3-way logouts (`current`, `others`, `all`), device heartbeat tracking, and outbox audit events.
- [x] **Permission-First Security Context**: Role-to-permission set mapping, fine-grained capability checks (`claims:read`, `reports:approve`), and `SecurityContext` dependency injection.

---

## 🏢 v1.2.0 — Multi-Tenant SaaS Architecture 🏢
> 📦 **Specification Package**: [`roadmap/v1.2-multitenant/`](roadmap/v1.2-multitenant/)
- [ ] **Organization & Team Isolation**: Tenant-scoped database schemas and organization-level RBAC.
- [ ] **Team Invitations**: Invitation workflows with role assignments (`Admin`, `Lead Reviewer`, `Reviewer`).
- [ ] **Project Isolation**: Tenant-scoped compliance project namespaces and audit boundaries.

---

## 🔌 v1.3.0 — Enterprise Integrations & Connectors 🔌
> 📦 **Specification Package**: [`roadmap/v1.3-integrations/`](roadmap/v1.3-integrations/)
- [ ] **Issue Tracker Sync**: Automatic creation and status synchronization with Jira and GitHub Issues.
- [ ] **Messaging Notifications**: Webhook event dispatchers for Slack and Microsoft Teams alerts.
- [ ] **Cloud Object Storage**: Direct presigned URL uploads to AWS S3 and Cloudflare R2.

---

## 📈 v1.4.0 — Platform Reliability & Observability 📊
> 📦 **Specification Package**: [`roadmap/v1.4-observability/`](roadmap/v1.4-observability/)
- [ ] **Distributed Tracing**: OpenTelemetry instrumentation with Jaeger trace propagation.
- [ ] **Metrics & Dashboards**: Grafana Cloud dashboard templates for P95 latency and retrieval recall.
- [ ] **Error Tracking & Alerting**: Production exception capture via Sentry and Prometheus alert manager.

---

## ⚙️ v1.5.0 — Policy Engine & Admin Operational Console ⚙️
> 📦 **Specification Package**: [`roadmap/v1.5-policy-engine/`](roadmap/v1.5-policy-engine/)
- [ ] **Configurable Approval Rules**: Automated enforcement gates (e.g. require dual approval for high-risk claims, block publication of unsupported claims).
- [ ] **Automatic Risk Escalation**: Automatic escalation of unsupported or high-risk claims to lead reviewers.
- [ ] **Workflow Event Automation**: Automated post-approval actions (compile PDF → upload S3 → create Jira ticket → send Slack alert).
- [ ] **Admin Operational Console**: Dedicated dashboard for User CRUD, Organization Management, API Key provisioning, Audit Log viewing, Worker Queue monitoring, and Vector Collection management.

---

## 🌟 v2.0.0 — AI-Native Enterprise SaaS & Knowledge Graph 🚀
> 📦 **Specification Package**: [`roadmap/v2.0-ai-platform/`](roadmap/v2.0-ai-platform/)
- [ ] **Compliance Knowledge Graph**: Graph-based entity modeling (`Requirement` -- supported by --> `Evidence` -- referenced in --> `Report` -- verified by --> `Reviewer`).
- [ ] **Real-Time WebSockets**: Live reviewer presence indicators, real-time comment streams, and collaborative editing.
- [ ] **Multi-Agent Reasoning Pipeline**: Centralized agent orchestration:
  - 🔍 *Requirement Analysis Agent*: Extracts regulatory requirements from standard PDFs.
  - 🎯 *Evidence Retrieval Agent*: Executes hybrid vector retrieval and reranking.
  - ⚖️ *Verification Agent*: Evaluates claim evidence against regulatory criteria.
  - ⚠️ *Risk Assessment Agent*: Computes casualty risk metrics and risk matrix scores.
  - 📝 *Report Drafting Agent*: Synthesizes structured compliance reports.
