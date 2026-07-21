# Test Plan — Version 1.1: Authentication & Session Identity

## Unit Tests
- `test_jwt_service_encode_decode_rs256()`: Verify RS256 token signing and signature verification with public key.
- `test_jwt_service_rejects_expired_token()`: Ensure expired access tokens raise `TokenExpiredError`.
- `test_refresh_token_hash_generation()`: Confirm refresh tokens are correctly hashed with SHA-256.

## Integration Tests
- `test_oauth_callback_creates_new_user()`: Simulate Google callback code exchange and verify `User` creation.
- `test_refresh_token_rotation_success()`: Exchange valid refresh token, verify new token issued and old token revoked.
- `test_refresh_token_replay_revokes_family()`: Present previously used refresh token and verify all tokens in family are revoked.

## API Endpoint Tests
- `test_get_me_returns_profile()`: Send valid Bearer header to `GET /auth/me` and assert 200 OK with user profile.
- `test_get_me_unauthorized_without_header()`: Request `GET /auth/me` without header and assert 401 Unauthorized.
