import pytest
from datetime import datetime, timezone, timedelta

from auth.repositories.user_repository import UserRepository
from auth.repositories.token_repository import TokenRepository
from database.models.enums import UserStatus
from database.models.session_model import SessionModel


@pytest.mark.asyncio
async def test_user_repository_create_google_user_and_find(db_session):
    """Test UserRepository creation of Google user and domain lookup operations."""
    repo = UserRepository(db_session)
    user = await repo.create_google_user(
        email="google_test@complianceos.io",
        full_name="Google Tester",
        provider_user_id="google_sub_999",
        avatar_url="https://example.com/avatar.png",
    )
    assert user.id is not None
    # role is now on OrganizationMembership — not on User in v1.2

    found_by_email = await repo.find_by_email("GOOGLE_TEST@COMPLIANCEOS.IO ")
    assert found_by_email is not None
    assert found_by_email.id == user.id

    found_by_prov = await repo.find_by_provider("GOOGLE", "google_sub_999")
    assert found_by_prov is not None
    assert found_by_prov.id == user.id


@pytest.mark.asyncio
async def test_user_repository_lifecycle_updates(db_session):
    """Test UserRepository lifecycle methods (record_login, deactivate, activate).

    Note: change_role was removed in v1.2. Role is now managed via OrganizationMembership.
    """
    repo = UserRepository(db_session)
    user = await repo.create_google_user(
        email="lifecycle@complianceos.io",
        full_name="Lifecycle User",
        provider_user_id="sub_life_123",
    )

    await repo.record_login(user.id)
    refreshed = await repo.find_by_id(user.id)
    assert refreshed.login_count == 1
    assert refreshed.last_login_at is not None

    await repo.deactivate(user.id)
    refreshed = await repo.find_by_id(user.id)
    assert refreshed.is_active is False
    assert refreshed.status == "inactive"

    await repo.activate(user.id)
    refreshed = await repo.find_by_id(user.id)
    assert refreshed.is_active is True
    assert refreshed.status == "active"


@pytest.mark.asyncio
async def test_token_repository_refresh_and_family_revocation(db_session):
    """Test TokenRepository creation, rotation marking, and token family revocation."""
    user_repo = UserRepository(db_session)
    token_repo = TokenRepository(db_session)

    user = await user_repo.create_google_user(
        email="tok_family@complianceos.io",
        full_name="Token Family User",
        provider_user_id="sub_tok_fam",
    )

    now = datetime.now(timezone.utc)
    family_id = "family_xyz_123"

    t1 = await token_repo.create_refresh_token(
        user_id=user.id,
        token_family=family_id,
        token_hash="hash_token_1",
        expires_at=now + timedelta(days=7),
    )
    await token_repo.create_refresh_token(
        user_id=user.id,
        token_family=family_id,
        token_hash="hash_token_2",
        expires_at=now + timedelta(days=7),
    )

    await token_repo.mark_token_used(t1.id, replaced_by_hash="hash_token_2")
    t1_fetched = await token_repo.find_refresh_token_by_hash("hash_token_1")
    assert t1_fetched.replaced_by_token == "hash_token_2"
    assert t1_fetched.last_used_at is not None

    # Trigger family revocation on replay detection
    revoked_count = await token_repo.revoke_token_family(family_id)
    assert revoked_count == 2

    t2_fetched = await token_repo.find_refresh_token_by_hash("hash_token_2")
    assert t2_fetched.is_revoked is True
    assert t2_fetched.revoked_at is not None


@pytest.mark.asyncio
async def test_token_repository_session_lifecycle(db_session):
    """Test TokenRepository session creation, activity touch, listing, and revocation."""
    user_repo = UserRepository(db_session)
    token_repo = TokenRepository(db_session)

    user = await user_repo.create_google_user(
        email="session_user@complianceos.io",
        full_name="Session User",
        provider_user_id="sub_sess_user",
    )

    now = datetime.now(timezone.utc)
    session_obj = SessionModel(
        user_id=user.id,
        session_token_hash="sess_hash_abc_123",
        user_agent="Mozilla/5.0",
        ip_address="127.0.0.1",
        last_activity_at=now,
        expires_at=now + timedelta(hours=24),
    )
    await token_repo.create_session(session_obj)

    found_sess = await token_repo.find_by_token_hash("sess_hash_abc_123")
    assert found_sess is not None
    assert found_sess.user_id == user.id

    touched = await token_repo.touch_activity(found_sess.id)
    assert touched is True

    active_sessions = await token_repo.list_active_by_user(user.id)
    assert len(active_sessions) == 1

    revoked = await token_repo.revoke_session(found_sess.id)
    assert revoked is True

    found_after_revoke = await token_repo.find_by_token_hash("sess_hash_abc_123")
    assert found_after_revoke is None
