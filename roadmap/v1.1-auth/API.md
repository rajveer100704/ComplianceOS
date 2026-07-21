# API Specification — Version 1.1: Authentication & Session Identity

## Endpoints Summary

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/auth/login/google` | Initiate Google OAuth2 PKCE login redirect | None |
| `GET` | `/auth/callback/google` | Handle Google OAuth2 callback and issue tokens | None |
| `POST` | `/auth/token/refresh` | Exchange refresh token for new access token | Bearer / Cookie |
| `POST` | `/auth/logout` | Revoke active refresh token and end session | Bearer |
| `GET` | `/auth/me` | Retrieve authenticated user profile | Bearer |

## Request / Response Schemas

### GET /auth/callback/google
- **Query Params**: `code` (string), `state` (string)
- **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "rt_8f1a2b3c...",
  "user": {
    "id": "usr_99a8b7",
    "email": "reviewer@complianceos.io",
    "name": "Jane Doe",
    "role": "Reviewer"
  }
}
```

### POST /auth/token/refresh
- **Request Body**:
```json
{
  "refresh_token": "rt_8f1a2b3c..."
}
```
- **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "rt_new_token_77b6a..."
}
```
