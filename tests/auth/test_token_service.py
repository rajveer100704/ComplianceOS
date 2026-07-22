import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta

from auth.services.token_service import TokenService
from auth.services.jwt_service import JWTService
from auth.repositories.user_repository import UserRepository
from auth.repositories.token_repository import TokenRepository
from auth.utils import hash_refresh_token
from auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TokenReplayError,
)
from database.models.refresh_token import RefreshToken


@pytest_asyncio.fixture
async def sample_user(db_session):
    """Creates a sample user for testing token operations."""
    repo = UserRepository(db_session)
    user = await repo.create_google_user(
        email="token_user@complianceos.io",
        provider_user_id="g_token_user_123",
        full_name="Token Test User",
    )
    await db_session.commit()
    return user


# v1.2: role is now on OrganizationMembership, not User.
# Token service tests use a fixed role string for JWT payload testing.
_TEST_ROLE = "reviewer"


@pytest.mark.asyncio
async def test_issue_token_pair_returns_valid_access_and_refresh_tokens(
    db_session, sample_user
):
    """Test issuing access and refresh token pair."""
    service = TokenService(db_session)

    pair = await service.issue_token_pair(
        user_id=sample_user.id,
        email=sample_user.email,
        role=_TEST_ROLE,
        device_name="Chrome MacOS",
    )

    assert "access_token" in pair
    assert "refresh_token" in pair
    assert pair["token_type"] == "Bearer"
    assert pair["expires_in"] == 900
    assert "expires_at" in pair
    assert pair["refresh_token"].startswith("rt_")

    # Verify access token decoded via JWTService
    jwt_svc = JWTService()
    payload = jwt_svc.verify_access_token(pair["access_token"])
    assert payload["sub"] == sample_user.id

    # Verify refresh token in DB stored as HMAC-SHA256 hash
    repo = TokenRepository(db_session)
    token_hash = hash_refresh_token(pair["refresh_token"])
    db_token = await repo.find_refresh_token_by_hash(token_hash)
    assert db_token is not None
    assert db_token.user_id == sample_user.id
    assert db_token.rotation_count == 0
    assert db_token.is_revoked is False


@pytest.mark.asyncio
async def test_rotate_refresh_token_success(db_session, sample_user):
    """Test single-use refresh token rotation."""
    service = TokenService(db_session)

    pair1 = await service.issue_token_pair(
        user_id=sample_user.id,
        email=sample_user.email,
        role=_TEST_ROLE,
    )
    raw_rt1 = pair1["refresh_token"]

    # Rotate RT1 -> RT2
    pair2 = await service.rotate_refresh_token(
        raw_refresh_token=raw_rt1,
        email=sample_user.email,
        role=_TEST_ROLE,
    )
    raw_rt2 = pair2["refresh_token"]

    assert raw_rt2 != raw_rt1
    assert raw_rt2.startswith("rt_")

    # Verify RT1 is marked used & replaced in DB
    repo = TokenRepository(db_session)
    rt1_hash = hash_refresh_token(raw_rt1)
    db_rt1 = await repo.find_refresh_token_by_hash(rt1_hash)
    assert db_rt1.last_used_at is not None
    assert db_rt1.replaced_by_token == hash_refresh_token(raw_rt2)

    # Verify RT2 created in same family with rotation_count = 1
    db_rt2 = await repo.find_refresh_token_by_hash(hash_refresh_token(raw_rt2))
    assert db_rt2.token_family == db_rt1.token_family
    assert db_rt2.rotation_count == 1


@pytest.mark.asyncio
async def test_replay_used_refresh_token_revokes_family(db_session, sample_user):
    """Test replaying a previously rotated refresh token outside grace period triggers family revocation."""
    service = TokenService(db_session)

    pair1 = await service.issue_token_pair(
        user_id=sample_user.id,
        email=sample_user.email,
        role=_TEST_ROLE,
    )
    raw_rt1 = pair1["refresh_token"]

    # Rotate RT1 -> RT2
    pair2 = await service.rotate_refresh_token(
        raw_refresh_token=raw_rt1,
        email=sample_user.email,
        role=_TEST_ROLE,
    )
    raw_rt2 = pair2["refresh_token"]

    # Manually backdate RT1's last_used_at to bypass 10-second grace window
    repo = TokenRepository(db_session)
    db_rt1 = await repo.find_refresh_token_by_hash(hash_refresh_token(raw_rt1))
    db_rt1.last_used_at = datetime.now(timezone.utc) - timedelta(seconds=30)
    await db_session.flush()

    # Replay RT1 -> Should raise TokenReplayError & revoke whole family (including RT2)
    with pytest.raises(TokenReplayError):
        await service.rotate_refresh_token(
            raw_refresh_token=raw_rt1,
            email=sample_user.email,
            role=_TEST_ROLE,
        )

    # Verify both RT1 and RT2 are marked revoked in DB
    db_rt1_after = await repo.find_refresh_token_by_hash(hash_refresh_token(raw_rt1))
    db_rt2_after = await repo.find_refresh_token_by_hash(hash_refresh_token(raw_rt2))
    assert db_rt1_after.is_revoked is True
    assert db_rt2_after.is_revoked is True


@pytest.mark.asyncio
async def test_concurrent_refresh_within_grace_period_succeeds(db_session, sample_user):
    """Test that concurrent refresh requests within grace period succeed without triggering replay error."""
    service = TokenService(db_session)

    pair1 = await service.issue_token_pair(
        user_id=sample_user.id,
        email=sample_user.email,
        role=_TEST_ROLE,
    )
    raw_rt1 = pair1["refresh_token"]

    # Initial rotation
    await service.rotate_refresh_token(
        raw_refresh_token=raw_rt1,
        email=sample_user.email,
        role=_TEST_ROLE,
    )

    # Concurrent request immediately following (0.1s later, within 10s grace period)
    grace_pair = await service.rotate_refresh_token(
        raw_refresh_token=raw_rt1,
        email=sample_user.email,
        role=_TEST_ROLE,
    )
    assert "access_token" in grace_pair


@pytest.mark.asyncio
async def test_expired_refresh_token_raises_token_expired_error(
    db_session, sample_user
):
    """Test that past-expiry refresh tokens raise TokenExpiredError."""
    service = TokenService(db_session)

    # Manually create an expired refresh token satisfying expires_at > created_at
    raw_rt = "rt_expired_12345"
    rt_hash = hash_refresh_token(raw_rt)
    created_time = datetime.now(timezone.utc) - timedelta(days=10)
    expired_time = datetime.now(timezone.utc) - timedelta(days=3)

    token = RefreshToken(
        user_id=sample_user.id,
        token_family="family_exp",
        token_hash=rt_hash,
        expires_at=expired_time,
        created_at=created_time,
    )
    db_session.add(token)
    await db_session.flush()

    with pytest.raises(TokenExpiredError):
        await service.rotate_refresh_token(
            raw_refresh_token=raw_rt,
            email=sample_user.email,
            role=_TEST_ROLE,
        )


@pytest.mark.asyncio
async def test_invalid_token_format_raises_invalid_token_error(db_session, sample_user):
    """Test that non-existent or malformed refresh tokens raise InvalidTokenError."""
    service = TokenService(db_session)

    with pytest.raises(InvalidTokenError):
        await service.rotate_refresh_token(
            raw_refresh_token="",
            email=sample_user.email,
            role=_TEST_ROLE,
        )

    with pytest.raises(InvalidTokenError):
        await service.rotate_refresh_token(
            raw_refresh_token="rt_non_existent_token_9999",
            email=sample_user.email,
            role=_TEST_ROLE,
        )


@pytest.mark.asyncio
async def test_revoke_all_for_user(db_session, sample_user):
    """Test revoking all active refresh tokens for a user (Logout All)."""
    service = TokenService(db_session)

    await service.issue_token_pair(
        user_id=sample_user.id, email=sample_user.email, role=_TEST_ROLE
    )
    await service.issue_token_pair(
        user_id=sample_user.id, email=sample_user.email, role=_TEST_ROLE
    )

    revoked_count = await service.revoke_all_for_user(sample_user.id)
    assert revoked_count == 2


@pytest.mark.asyncio
async def test_cleanup_expired_tokens(db_session, sample_user):
    """Test cleaning up expired refresh tokens."""
    service = TokenService(db_session)

    # Create expired token satisfying expires_at > created_at
    raw_rt = "rt_clean_expired"
    created_time = datetime.now(timezone.utc) - timedelta(days=10)
    expired_time = datetime.now(timezone.utc) - timedelta(days=3)

    token = RefreshToken(
        user_id=sample_user.id,
        token_family="family_clean",
        token_hash=hash_refresh_token(raw_rt),
        expires_at=expired_time,
        created_at=created_time,
    )
    db_session.add(token)
    await db_session.flush()

    cleaned_count = await service.cleanup_expired()
    assert cleaned_count >= 1
