import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from database.models.user import User
from database.models.oauth_account import OAuthAccount
from database.models.refresh_token import RefreshToken
from database.models.session_model import SessionModel
from database.models.enums import UserRole, UserStatus


@pytest.mark.asyncio
async def test_create_user_and_oauth_account(db_session):
    """Verify User and OAuthAccount model persistence and relationship cascade."""
    user = User(
        email="reviewer@complianceos.io",
        full_name="Jane Reviewer",
        role=UserRole.LEAD_REVIEWER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    await db_session.flush()

    oauth_acc = OAuthAccount(
        user_id=user.id,
        provider="google",
        provider_user_id="google_sub_12345",
        provider_email="reviewer@complianceos.io",
    )
    db_session.add(oauth_acc)
    await db_session.flush()

    await db_session.refresh(user, ["oauth_accounts"])
    assert user.id is not None
    assert user.role == UserRole.LEAD_REVIEWER
    assert len(user.oauth_accounts) == 1
    assert user.oauth_accounts[0].provider == "google"


@pytest.mark.asyncio
async def test_duplicate_user_email_raises_error(db_session):
    """Verify unique constraint on user email."""
    u1 = User(email="duplicate@complianceos.io", full_name="User One")
    u2 = User(email="duplicate@complianceos.io", full_name="User Two")
    db_session.add(u1)
    await db_session.flush()

    db_session.add(u2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_duplicate_oauth_provider_user_id_raises_error(db_session):
    """Verify unique constraint on (provider, provider_user_id)."""
    u1 = User(email="u1@complianceos.io", full_name="User One")
    u2 = User(email="u2@complianceos.io", full_name="User Two")
    db_session.add_all([u1, u2])
    await db_session.flush()

    acc1 = OAuthAccount(user_id=u1.id, provider="google", provider_user_id="sub_same")
    acc2 = OAuthAccount(user_id=u2.id, provider="google", provider_user_id="sub_same")
    db_session.add(acc1)
    await db_session.flush()

    db_session.add(acc2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_cascade_delete_user_removes_tokens_and_sessions(db_session):
    """Verify deleting a User cascades to OAuth accounts, refresh tokens, and sessions."""
    now = datetime.now(timezone.utc)
    user = User(email="cascade@complianceos.io", full_name="Cascade User")
    db_session.add(user)
    await db_session.flush()

    oauth_acc = OAuthAccount(
        user_id=user.id, provider="google", provider_user_id="sub_casc"
    )
    refresh_tok = RefreshToken(
        user_id=user.id,
        token_family="family_casc",
        token_hash="hash_casc_123",
        expires_at=now + timedelta(days=7),
    )
    sess = SessionModel(
        user_id=user.id,
        session_token_hash="sess_hash_123",
        last_activity_at=now,
        expires_at=now + timedelta(hours=24),
    )
    db_session.add_all([oauth_acc, refresh_tok, sess])
    await db_session.flush()

    await db_session.delete(user)
    await db_session.flush()

    res_oauth = await db_session.execute(
        select(OAuthAccount).where(OAuthAccount.user_id == user.id)
    )
    res_tokens = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    res_sess = await db_session.execute(
        select(SessionModel).where(SessionModel.user_id == user.id)
    )

    assert len(res_oauth.scalars().all()) == 0
    assert len(res_tokens.scalars().all()) == 0
    assert len(res_sess.scalars().all()) == 0
