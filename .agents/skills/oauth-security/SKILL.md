---
name: oauth-security
description: >
  Use when implementing OAuth-specific security controls: PKCE, state parameter
  validation, token replay prevention, refresh token rotation security, RS256
  key management, and OAuth callback hardening.
---

# OAuth Security Skill

## When to Use

- Implementing OAuth2 callback security.
- Adding PKCE to authorization code flows.
- Implementing refresh token replay detection.
- Configuring RS256 key rotation.
- Hardening OAuth state parameter handling.

## Security Controls

### 1. State Parameter (CSRF Prevention)

```python
import secrets

# Generate
state = secrets.token_urlsafe(32)  # ≥ 32 bytes
# Store in session/cookie before redirect
# Verify on callback — reject if mismatch
```

- Generate cryptographically random state (≥ 32 bytes).
- Store server-side (session or signed cookie) before redirect.
- Verify exact match on callback. Reject on mismatch.
- Single-use: delete state after verification.

### 2. PKCE (Proof Key for Code Exchange)

```python
import hashlib, base64, secrets

code_verifier = secrets.token_urlsafe(64)  # 43-128 chars
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()
# Send code_challenge with auth request
# Send code_verifier with token exchange
```

- Always use S256 method (not plain).
- Store `code_verifier` server-side alongside state.
- Send `code_challenge` in authorization request.
- Send `code_verifier` in token exchange request.

### 3. Refresh Token Replay Detection

```
Token Family: user_123_family_abc
├── refresh_token_1 (issued) → used → invalidated
├── refresh_token_2 (issued) → used → invalidated
├── refresh_token_3 (issued) → active
│
│   If refresh_token_1 is presented again:
│   └── REPLAY DETECTED → Revoke entire family
│       └── Force re-authentication
```

- Each refresh creates a new token and invalidates the previous one.
- Track token family (lineage).
- If an already-used token is presented → revoke the entire family.
- Log replay attempts for security monitoring.

### 4. RS256 Key Management

- Use asymmetric RS256 (RSA + SHA-256) for JWT signing.
- Private key: stored securely, never in source code.
- Public key: available at `/.well-known/jwks.json` for verification.
- Support key rotation via `kid` (Key ID) header in JWTs.
- Old keys remain valid for verification during rotation window.

### 5. Callback Hardening

- Validate redirect URI matches pre-registered values exactly.
- Exchange authorization code immediately (single-use, short-lived).
- Verify `id_token` signature against provider's JWKS.
- Check `iss`, `aud`, `exp`, `nonce` claims in `id_token`.
- Rate limit callback endpoint (≤ 10/min per IP).

## Checklist

- [ ] State parameter generated with `secrets.token_urlsafe(32)`.
- [ ] PKCE implemented with S256 method.
- [ ] Refresh tokens stored as SHA-256 hashes.
- [ ] Refresh token rotation implemented.
- [ ] Replay detection revokes token family.
- [ ] RS256 signing with key rotation support.
- [ ] Callback redirect URI validated.
- [ ] Authorization code exchanged immediately.
- [ ] id_token signature verified.
- [ ] Rate limiting on auth endpoints.

## References

- [docs/security/SECURITY_ENGINEERING.md](../../docs/security/SECURITY_ENGINEERING.md)
