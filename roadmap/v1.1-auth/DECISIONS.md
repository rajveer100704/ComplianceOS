# Architectural Decisions Log — Version 1.1: Authentication & Session Identity

- **Decision 1: Google OAuth2 First**: Selected Google OAuth2 as the initial identity provider due to OIDC standard compliance and universal adoption across engineering organizations.
- **Decision 2: RS256 Asymmetric Signing**: Chose RS256 over HS256 to allow microservices and worker nodes to verify access tokens using only the public key, keeping the private key isolated on the auth service.
- **Decision 3: Single-Use Refresh Token Rotation**: Implemented automatic refresh token rotation on every `/auth/token/refresh` request to limit the window of vulnerability for stolen refresh tokens.
- **Decision 4: Hash Refresh Tokens at Rest**: Stored refresh tokens as SHA-256 hashes in the database so a database breach does not compromise active user sessions.
