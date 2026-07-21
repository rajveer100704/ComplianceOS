---
name: multitenancy
description: >
  Use when implementing multi-tenant features: organization models, team management,
  invitation workflows, tenant-scoped RBAC, project isolation, and tenant middleware.
  Loaded for v1.2 implementation.
---

# Multi-Tenancy Skill

## When to Use

- Creating organization and team models.
- Implementing tenant isolation in queries.
- Adding invitation workflows.
- Implementing organization-level RBAC.
- Adding tenant context middleware.

## Data Model

```
Organization (tenant root)
├── id, name, slug, plan, created_at
├── has many → Team
├── has many → Membership
└── has many → Project (ComplianceRequest scoped)

Team
├── id, organization_id, name, description
└── has many → TeamMembership

Membership
├── id, organization_id, user_id, role
├── role: "owner" | "admin" | "member" | "viewer"
└── invited_by, joined_at

Invitation
├── id, organization_id, email, role
├── token (SHA-256 hashed), expires_at
├── status: "pending" | "accepted" | "expired" | "revoked"
└── invited_by
```

## Tenant Isolation Rules

- Every query must be scoped to the current tenant.
- Middleware extracts `organization_id` from JWT claims or session.
- Services receive `organization_id` as a parameter, never from global state.
- Repository methods always include `where(Model.organization_id == org_id)`.
- Cross-tenant access is always denied. No exceptions.

## Invitation Lifecycle

```
Admin sends invitation
       │
       ▼
Invitation created (token generated, hashed, stored)
       │
       ▼
Email sent with invitation link
       │
       ▼
User clicks link → /auth/invite/{token}
       │
       ├── Token verified (hash match, not expired, not used)
       ├── User created or linked
       ├── Membership created with invited role
       ├── Invitation marked "accepted"
       │
       ▼
User redirected to organization dashboard
```

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md) §3 (Domain Ownership)
- [docs/security/SECURITY_ENGINEERING.md](../../docs/security/SECURITY_ENGINEERING.md)
