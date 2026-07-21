# Risk Assessment — Version 1.2: Multi-Tenant SaaS Architecture

| Risk | Mitigation |
| :--- | :--- |
| **Cross-Tenant Data Leakage** | Enforce `organization_id` in repository base query class; automated isolation test suite. |
| **Orphaned Organizations** | Require at least 1 `Owner` role per organization. |
