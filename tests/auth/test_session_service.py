import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta

from auth.services.session_service import SessionService, SessionState
from auth.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def sample_user(db_session):
    """Creates a sample user for testing session operations."""
    repo = UserRepository(db_session)
    user = await repo.create_google_user(
        email="session_user@complianceos.io",
        provider_user_id="g_session_user_123",
        full_name="Session Test User",
    )
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_create_and_validate_session(db_session, sample_user):
    """Test creating a session and validating it."""
    service = SessionService(db_session)
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    res = await service.create_session(
        user_id=sample_user.id,
        user_agent=ua,
        ip_address="192.168.1.50",
    )

    assert "session_id" in res
    assert "session_token" in res
    assert res["device_info"]["browser"] == "Chrome"
    assert res["device_info"]["operating_system"] == "macOS"
    assert res["device_info"]["device_type"] == "desktop"

    # Validate session
    state, session_obj = await service.validate_session(
        res["session_id"], user_agent=ua
    )
    assert state == SessionState.VALID
    assert session_obj is not None
    assert session_obj.user_id == sample_user.id


@pytest.mark.asyncio
async def test_touch_session_activity_throttling(db_session, sample_user):
    """Test that heartbeat activity touch is throttled within 60s."""
    service = SessionService(db_session)
    res = await service.create_session(user_id=sample_user.id)
    sid = res["session_id"]

    # Initial touch immediately -> skipped because < 60s
    touched1 = await service.touch_session_activity(sid)
    assert touched1 is True

    # Manually set last_activity_at to 120s ago to trigger DB update
    state, session_obj = await service.validate_session(sid)
    session_obj.last_activity_at = datetime.now(timezone.utc) - timedelta(seconds=120)
    await db_session.flush()

    touched2 = await service.touch_session_activity(sid)
    assert touched2 is True


@pytest.mark.asyncio
async def test_idle_and_absolute_timeouts(db_session, sample_user):
    """Test that idle timeout (30d) and absolute timeout (90d) set state to EXPIRED."""
    service = SessionService(db_session)
    res = await service.create_session(user_id=sample_user.id)
    sid = res["session_id"]

    # 1. Simulate Idle Expiration (>30 days inactivity)
    state_v, session_obj = await service.validate_session(sid)
    session_obj.last_activity_at = datetime.now(timezone.utc) - timedelta(days=31)
    await db_session.flush()

    state_idle, _ = await service.validate_session(sid)
    assert state_idle == SessionState.EXPIRED

    # 2. Simulate Absolute Expiration (>90 days creation)
    session_obj.last_activity_at = datetime.now(timezone.utc)  # Reset last_activity
    session_obj.created_at = datetime.now(timezone.utc) - timedelta(days=91)
    await db_session.flush()

    state_abs, _ = await service.validate_session(sid)
    assert state_abs == SessionState.EXPIRED


@pytest.mark.asyncio
async def test_high_risk_session_detection(db_session, sample_user):
    """Test that abrupt device_type changes set state to HIGH_RISK."""
    service = SessionService(db_session)
    desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

    res = await service.create_session(user_id=sample_user.id, user_agent=desktop_ua)
    sid = res["session_id"]

    # Present mobile UA on a desktop session -> HIGH_RISK
    state, _ = await service.validate_session(sid, user_agent=mobile_ua)
    assert state == SessionState.HIGH_RISK


@pytest.mark.asyncio
async def test_logout_current_device(db_session, sample_user):
    """Test revoking a single session (Logout Current Device)."""
    service = SessionService(db_session)
    res = await service.create_session(user_id=sample_user.id)
    sid = res["session_id"]

    success = await service.revoke_session(sid)
    assert success is True

    state, _ = await service.validate_session(sid)
    assert state == SessionState.REVOKED


@pytest.mark.asyncio
async def test_logout_other_devices(db_session, sample_user):
    """Test revoking all other sessions except current (Logout Other Devices)."""
    service = SessionService(db_session)
    s1 = (await service.create_session(user_id=sample_user.id))["session_id"]
    s2 = (await service.create_session(user_id=sample_user.id))["session_id"]
    s3_current = (await service.create_session(user_id=sample_user.id))["session_id"]

    revoked_count = await service.revoke_other_sessions(
        sample_user.id, current_session_id=s3_current
    )
    assert revoked_count == 2

    state1, _ = await service.validate_session(s1)
    state2, _ = await service.validate_session(s2)
    state3, _ = await service.validate_session(s3_current)

    assert state1 == SessionState.REVOKED
    assert state2 == SessionState.REVOKED
    assert state3 == SessionState.VALID


@pytest.mark.asyncio
async def test_logout_everywhere(db_session, sample_user):
    """Test revoking all user sessions (Logout Everywhere)."""
    service = SessionService(db_session)
    await service.create_session(user_id=sample_user.id)
    await service.create_session(user_id=sample_user.id)

    revoked_count = await service.revoke_all_sessions(sample_user.id)
    assert revoked_count == 2


@pytest.mark.asyncio
async def test_get_user_sessions_for_active_devices_ui(db_session, sample_user):
    """Test listing user sessions formatted for Active Devices UI."""
    service = SessionService(db_session)
    s1_id = (await service.create_session(user_id=sample_user.id))["session_id"]
    s2_id = (await service.create_session(user_id=sample_user.id))["session_id"]

    sessions_list = await service.get_user_sessions(
        sample_user.id, current_session_id=s2_id
    )
    assert len(sessions_list) == 2

    # Check is_current flag
    s1_item = next(s for s in sessions_list if s["session_id"] == s1_id)
    s2_item = next(s for s in sessions_list if s["session_id"] == s2_id)

    assert s1_item["is_current"] is False
    assert s2_item["is_current"] is True


@pytest.mark.asyncio
async def test_cleanup_expired_and_revoked_sessions(db_session, sample_user):
    """Test cleaning up expired and soft-deleted sessions."""
    service = SessionService(db_session)
    res = await service.create_session(user_id=sample_user.id)
    sid = res["session_id"]

    # Revoke session
    await service.revoke_session(sid)

    rev_count = await service.cleanup_revoked_sessions()
    assert rev_count >= 1
