# Risk Assessment — Version 1.1: Authentication & Session Identity

| Risk | Impact | Probability | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **OAuth Callback CSRF Replay** | High | Medium | Enforce single-use, cryptographically random `state` parameter bound to session cookie. |
| **Refresh Token Leakage** | Critical | Low | Store refresh tokens as SHA-256 hashes in DB; enforce single-use token rotation. |
| **Token Family Replay Attack** | Critical | Low | Replay detection: using an already-used refresh token revokes the entire token family. |
| **Clock Skew Mismatch** | Medium | Medium | Include 30-second leeway in JWT expiration validation. |
| **Google OIDC Downtime** | High | Low | Catch connection timeouts and return descriptive 502 error; maintain active session window. |
