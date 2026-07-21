# Implementation Guide — Version 1.2: Multi-Tenant SaaS Architecture

1. **Step 1**: Create `Organization` and `Membership` models, migration scripts.
2. **Step 2**: Add `TenantMiddleware` to extract `org_id` from request headers/claims.
3. **Step 3**: Update all repository filters to require `organization_id`.
4. **Step 4**: Implement `/orgs` and `/orgs/{org_id}/invitations` endpoints.
5. **Step 5**: Write isolation verification test suite.
