# API Specification — Version 1.2: Multi-Tenant SaaS Architecture

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/orgs` | Create a new organization workspace |
| `GET` | `/orgs/me` | List organizations for current authenticated user |
| `POST` | `/orgs/{org_id}/invitations` | Invite a new team member with role |
| `GET` | `/orgs/{org_id}/members` | List workspace team members and roles |
