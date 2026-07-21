# ADR 0005: Adoption of Authlib and RS256 Asymmetric JWT Verification

## Date
2026-07-21

## Status
Accepted

## Context & Problem Statement
ComplianceOS requires an enterprise-grade authentication stack supporting OAuth2 OIDC flows and signed JWT tokens. We need an open-source, FastAPI-compatible solution without vendor lock-in.

## Considered Options
1. **Authlib + PyJWT (Selected)**
2. **Clerk / Auth0 (Hosted SaaS)**
3. **Supabase Auth (Database-bound)**

## Decision Outcome
Chosen option: **Authlib + PyJWT**, because Authlib natively handles OAuth2 client flows with PKCE and state validation, while PyJWT provides clean RS256 token verification without hosted vendor dependencies.

### Positive Consequences
- Zero external vendor dependencies or monthly SaaS costs.
- Fully compatible with FastAPI `Depends()` and ASGI middleware.
- Open-source, self-hosted deployment ready.

### Negative Consequences
- Team is responsible for managing RS256 private/public key pairs and key rotation.
