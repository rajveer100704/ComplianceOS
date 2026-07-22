import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from config.settings import settings
from auth.router import router as auth_router
from auth.dependencies import get_db_session
from auth.repositories.user_repository import UserRepository

# Create a clean test FastAPI app to test auth_router without importing heavy ML dependencies
app = FastAPI()
app.include_router(auth_router)


@pytest.fixture(autouse=True)
def mock_outbox_events():
    """Mocks EventPublisher.publish_event to prevent external DB connection attempts in tests."""
    with patch("database.events.EventPublisher.publish_event", new_callable=AsyncMock):
        yield


@pytest.mark.asyncio
async def test_jwks_endpoint_returns_valid_keys():
    """Test GET /.well-known/jwks.json returns public key array and caching headers."""
    client = TestClient(app)
    resp = client.get("/.well-known/jwks.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "keys" in data
    assert len(data["keys"]) >= 1
    assert "Cache-Control" in resp.headers
    assert "ETag" in resp.headers


@pytest.mark.asyncio
async def test_google_login_initiation_endpoint(db_session):
    """Test GET /api/v1/auth/google/login returns authorization URL and sets oauth_state cookie."""

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        client = TestClient(app)
        resp = client.get("/api/v1/auth/google/login?redirect=false")
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "state" in data
        assert data["provider"] == "google"
        assert "oauth_state" in client.cookies
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_google_callback_and_me_flow(db_session):
    """Test end-to-end OAuth callback, cookie issuance, and /me profile retrieval."""

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        client = TestClient(app)

        # 1. Initiate Login to get state and set oauth_state cookie on client
        login_resp = client.get("/api/v1/auth/google/login?redirect=false")
        state = login_resp.json()["state"]

        # 2. Execute Callback with mock_code (client sends oauth_state cookie automatically)
        cb_resp = client.get(
            f"/api/v1/auth/google/callback?code=mock_code_123&state={state}"
        )
        if cb_resp.status_code != 200:
            print("CB_RESP_ERROR:", cb_resp.json())
        assert cb_resp.status_code == 200
        token_data = cb_resp.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert "access_token" in client.cookies
        assert "refresh_token" in client.cookies

        # 3. Call GET /api/v1/auth/me (client sends access_token cookie automatically)
        me_resp = client.get("/api/v1/auth/me")
        assert me_resp.status_code == 200
        profile = me_resp.json()
        from auth.enums import has_permission

        assert profile["email"].endswith("@complianceos.io")
        assert profile["role"].lower() in ("owner", "reviewer")
        assert has_permission(profile["permissions"], "claims:read") is True
        assert profile["current_session"] is not None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_google_callback_csrf_mismatch_raises_401(db_session):
    """Test callback with state mismatch raises 401 UNAUTHORIZED."""

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        client = TestClient(app)
        client.cookies.set("oauth_state", "expected_state_xyz")

        cb_resp = client.get(
            "/api/v1/auth/google/callback?code=mock_code_123&state=invalid_state_abc"
        )
        assert cb_resp.status_code == 401
        assert "CSRF protection failed" in cb_resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_token_rotation_endpoint(db_session, monkeypatch):
    """Test POST /api/v1/auth/refresh rotates single-use refresh token and sets new cookies."""
    monkeypatch.setattr(settings, "AUTH_REFRESH_REPLAY_GRACE_SECONDS", 0)

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        client = TestClient(app)

        # Obtain initial token pair via login -> callback
        login_resp = client.get("/api/v1/auth/google/login?redirect=false")
        state = login_resp.json()["state"]

        cb_resp = client.get(
            f"/api/v1/auth/google/callback?code=mock_code_ref123&state={state}"
        )
        assert cb_resp.status_code == 200
        orig_tokens = cb_resp.json()

        # Execute Refresh
        ref_resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": orig_tokens["refresh_token"]}
        )
        assert ref_resp.status_code == 200
        new_tokens = ref_resp.json()
        assert new_tokens["access_token"] != orig_tokens["access_token"]
        assert new_tokens["refresh_token"] != orig_tokens["refresh_token"]

        # Replay used refresh token outside grace period -> 401
        client.cookies.set("refresh_token", orig_tokens["refresh_token"])
        replay_resp = client.post("/api/v1/auth/refresh")
        assert replay_resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_logout_endpoint_clears_cookies_and_revokes_session(db_session):
    """Test POST /api/v1/auth/logout revokes session and clears cookies."""

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        client = TestClient(app)

        # Obtain tokens
        login_resp = client.get("/api/v1/auth/google/login?redirect=false")
        state = login_resp.json()["state"]

        cb_resp = client.get(
            f"/api/v1/auth/google/callback?code=mock_code_log123&state={state}"
        )
        tokens = cb_resp.json()

        # Logout
        logout_resp = client.post(
            "/api/v1/auth/logout",
            json={"scope": "current"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert logout_resp.status_code == 200
        assert logout_resp.json()["ok"] is True
        assert logout_resp.json()["revoked_count"] == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_suspended_user_profile_request_returns_403(db_session):
    """Test suspended user attempting /me endpoint returns 403 FORBIDDEN."""

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        repo = UserRepository(db_session)
        user = await repo.create_google_user(
            email="suspended_router@complianceos.io",
            provider_user_id="g_sus_router",
            full_name="Suspended Router User",
        )
        user.status = "suspended"
        user.is_active = False
        await db_session.flush()

        from auth.services.jwt_service import JWTService

        jwt_svc = JWTService()
        token = jwt_svc.generate_access_token(
            user_id=user.id,
            email=user.email,
            role="reviewer",
        )

        client = TestClient(app)
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert "suspended" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()
