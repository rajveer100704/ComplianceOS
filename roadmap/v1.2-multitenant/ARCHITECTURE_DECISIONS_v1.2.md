# Architecture Decision Record — v1.2 Multi-Tenant SaaS Architecture

> **Package**: `roadmap/v1.2-multitenant/`  
> **Status**: APPROVED & IMPLEMENTED  
> **Date**: 2026-07-22  

---

## 1. Why `OrganizationMembership` Owns Roles (Not `User`)

### Context
In single-tenant or basic systems, a `role` field is placed directly on the `User` entity (e.g., `user.role = "admin"`). However, in an enterprise SaaS platform, a single user often belongs to multiple organizations or workspaces (e.g. `Org A` as an `Owner`, `Org B` as a `Reviewer`, and `Org C` as an `Auditor`).

### Decision
`User.role` was completely deprecated and dropped from the database schema. Role assignments now live exclusively on the `OrganizationMembership` relationship model (`organization_id`, `user_id`, `role`).

### Rationale
- Enables seamless multi-tenant participation without conflicting permissions.
- Prevents security leaks where an admin in Org A inherits admin privileges when switching to Org B.
- Aligns with standard enterprise B2B SaaS patterns used by GitHub, Linear, Vercel, and Atlassian.

---

## 2. Why Repositories Are Tenant-Scoped

### Context
Database query leakage across tenant boundaries is the single highest-risk vulnerability in multi-tenant SaaS applications.

### Decision
All repositories within the `organizations/` module (`OrganizationRepository`, `OrganizationMembershipRepository`, `InvitationRepository`) accept `db` and `security_context` or explicitly scope every SQL query with `organization_id`.

### Rationale
- Guaranteed tenant data isolation at the persistence layer.
- Repository-level filter enforcement ensures that even if a service layer developer forgets to filter by org ID, queries cannot return rows belonging to another tenant.
- Soft-deleted entities (`is_deleted = True`) are automatically filtered out across all repository methods.

---

## 3. Why `SecurityContext` Carries `membership` and `organization`

### Context
FastAPI handlers and business services need access to the caller's identity, active organization, and resolved permissions.

### Decision
`SecurityContext` was extended with `membership: Optional[OrganizationMembership]` and `organization: Optional[Organization]`.

### Rationale
- Centralized dependency injection via `Depends(get_security_context)`.
- Eliminates duplicate database queries for the active membership within individual endpoint handlers.
- Gives authorization guards (`require_permission`, `require_role`) instant access to the exact membership role for the requested tenant.

---

## 4. Why `User` Has No Role Column

### Context
During initial planning, a fallback `user.role` column was considered for backwards compatibility.

### Decision
`users.role` and `users.organization_id` columns were permanently dropped in migration `a3f1c2d4e5b6_add_v1_2_multitenant_tables.py`.

### Rationale
- Maintaining two role fields (`User.role` and `OrganizationMembership.role`) introduces ambiguous source-of-truth bugs.
- Alembic migration backfills every existing user with a personal organization and `OWNER` membership prior to dropping the columns, ensuring 100% backwards compatibility and zero data loss.

---

## 5. Why `TenantMiddleware` Only Resolves Context (Does Not Block Requests)

### Context
Requests coming into FastAPI need to determine which organization context they target.

### Decision
`TenantMiddleware` inspects the request for `X-Organization-Id` header or `org_id` cookie and attaches `request.state.organization_id`. It does not perform database permission checks or return HTTP 403.

### Rationale
- Middleware remains lightweight and async non-blocking.
- Avoids querying the database twice per HTTP request (once in middleware and once in dependency injection).
- Domain permission enforcement and membership verification happen in `get_security_context()` and `OrganizationService`, where the full SQLAlchemy transaction session is available.

---

## 6. Why Invitations Use SHA-256 Token Hashing

### Context
Organization invitation links contain secret invitation tokens sent to user email addresses.

### Decision
The raw invitation token (`raw_token`) is generated using `secrets.token_urlsafe(32)`. Only its SHA-256 hash (`token_hash`) is saved to the database. The raw token is returned to the API caller only in `development` environment mode.

### Rationale
- Database compromise or SQL injection cannot expose active invitation tokens.
- Token resolution computes `hashlib.sha256(raw_token)` and looks up `token_hash`, preventing timing attacks.
- Single-use status lifecycle (`pending` → `accepted` / `expired` / `revoked`) prevents token replay attacks (returning HTTP 410 Gone on re-use).

---

## 7. Why Outbox Events Are Used (`organization.created`, `member.invited`, `member.joined`)

### Context
Actions within the organization module need to trigger audit logging, email notifications, and external webhooks (Slack/Jira).

### Decision
Business methods in `OrganizationService` publish domain events (`organization.created`, `member.invited`, `member.joined`) to the outbox table via `EventPublisher.publish_event(..., session=db)`.

### Rationale
- Transactional consistency: outbox records are committed in the same database transaction as the domain state change.
- Decouples background processing (email sending, Slack webhooks) from HTTP request handlers.
- Seamlessly integrates with the async background worker system established in v1.0.
