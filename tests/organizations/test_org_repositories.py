"""Integration tests for organization repositories using in-memory SQLite."""

import pytest
from datetime import datetime, timezone

from database.models.user import User
from database.models.organization import Organization
from database.models.enums import MembershipRole, InvitationStatus, OrganizationPlan
from database.repositories.organization_repository import OrganizationRepository
from database.repositories.membership_repository import OrganizationMembershipRepository
from database.repositories.invitation_repository import (
    InvitationRepository,
    generate_invitation_token,
)

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


async def _make_user(db_session, email: str = "alice@example.com") -> User:
    user = User(email=email, full_name="Alice", status="active", is_active=True)
    db_session.add(user)
    await db_session.flush()
    return user


async def _make_org(db_session, slug: str = "acme-corp") -> Organization:
    org = Organization(
        name="Acme Corp", slug=slug, plan=OrganizationPlan.FREE, is_active=True
    )
    db_session.add(org)
    await db_session.flush()
    return org


# ──────────────────────────────────────────────────────────────
# OrganizationRepository Tests
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_org_create_and_find_by_id(db_session):
    """Organization can be created and retrieved by ID."""
    repo = OrganizationRepository(db_session)
    org = await repo.create(name="Acme", slug="acme", created_by=None)
    await db_session.flush()

    found = await repo.find_by_id(org.id)
    assert found is not None
    assert found.name == "Acme"
    assert found.slug == "acme"


@pytest.mark.asyncio
async def test_org_find_by_slug(db_session):
    """Organization can be retrieved by unique slug."""
    repo = OrganizationRepository(db_session)
    await repo.create(name="Slug Corp", slug="slug-corp")
    await db_session.flush()

    found = await repo.find_by_slug("slug-corp")
    assert found is not None
    assert found.name == "Slug Corp"


@pytest.mark.asyncio
async def test_org_slug_exists(db_session):
    """slug_exists returns True for taken slugs."""
    repo = OrganizationRepository(db_session)
    await repo.create(name="MyOrg", slug="my-org")
    await db_session.flush()

    assert await repo.slug_exists("my-org") is True
    assert await repo.slug_exists("other-org") is False


@pytest.mark.asyncio
async def test_org_list_for_user(db_session):
    """list_for_user returns only orgs the user has a membership in."""
    user = await _make_user(db_session)

    org_repo = OrganizationRepository(db_session)
    mem_repo = OrganizationMembershipRepository(db_session)

    org_a = await org_repo.create(name="Org A", slug="org-a")
    org_b = await org_repo.create(name="Org B", slug="org-b")
    await db_session.flush()

    # Only add user to org_a
    await mem_repo.create(
        organization_id=org_a.id,
        user_id=user.id,
        role=MembershipRole.OWNER,
        joined_at=datetime.now(timezone.utc),
    )
    await db_session.flush()

    orgs = await org_repo.list_for_user(user.id)
    org_ids = [o.id for o in orgs]
    assert org_a.id in org_ids
    assert org_b.id not in org_ids


@pytest.mark.asyncio
async def test_org_soft_delete(db_session):
    """Soft-deleted org is not returned by find_by_id."""
    repo = OrganizationRepository(db_session)
    org = await repo.create(name="DeleteMe", slug="delete-me")
    await db_session.flush()

    await repo.soft_delete(org.id)
    found = await repo.find_by_id(org.id)
    assert found is None


# ──────────────────────────────────────────────────────────────
# OrganizationMembershipRepository Tests
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_membership_create_and_find(db_session):
    """Membership can be created and found by org+user."""
    user = await _make_user(db_session)
    org = await _make_org(db_session)

    repo = OrganizationMembershipRepository(db_session)
    await repo.create(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.OWNER,
        joined_at=datetime.now(timezone.utc),
    )
    await db_session.flush()

    found = await repo.find_by_org_and_user(org.id, user.id)
    assert found is not None
    assert found.role == MembershipRole.OWNER


@pytest.mark.asyncio
async def test_membership_list_members(db_session):
    """list_members returns all active members of an org."""
    org = await _make_org(db_session)
    user_a = await _make_user(db_session, email="a@example.com")
    user_b = await _make_user(db_session, email="b@example.com")

    repo = OrganizationMembershipRepository(db_session)
    await repo.create(
        organization_id=org.id,
        user_id=user_a.id,
        role=MembershipRole.OWNER,
        joined_at=datetime.now(timezone.utc),
    )
    await repo.create(
        organization_id=org.id,
        user_id=user_b.id,
        role=MembershipRole.REVIEWER,
        joined_at=datetime.now(timezone.utc),
    )
    await db_session.flush()

    members = await repo.list_members(org.id)
    assert len(members) == 2


@pytest.mark.asyncio
async def test_membership_is_member(db_session):
    """is_member returns True for existing members, False otherwise."""
    user = await _make_user(db_session)
    org = await _make_org(db_session)
    other_user = await _make_user(db_session, email="other@example.com")

    repo = OrganizationMembershipRepository(db_session)
    await repo.create(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.REVIEWER,
        joined_at=datetime.now(timezone.utc),
    )
    await db_session.flush()

    assert await repo.is_member(org.id, user.id) is True
    assert await repo.is_member(org.id, other_user.id) is False


# ──────────────────────────────────────────────────────────────
# InvitationRepository Tests
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invitation_create_and_find_by_token_hash(db_session):
    """Invitation can be found by its SHA-256 token hash."""
    org = await _make_org(db_session)
    user = await _make_user(db_session)

    raw_token, token_hash = generate_invitation_token()
    repo = InvitationRepository(db_session)
    await repo.create(
        organization_id=org.id,
        email="invitee@example.com",
        role=MembershipRole.REVIEWER,
        token_hash=token_hash,
        invited_by=user.id,
    )
    await db_session.flush()

    found = await repo.find_by_token_hash(token_hash)
    assert found is not None
    assert found.email == "invitee@example.com"


@pytest.mark.asyncio
async def test_invitation_mark_accepted(db_session):
    """mark_accepted sets status to ACCEPTED and timestamps accepted_at."""
    org = await _make_org(db_session)
    user = await _make_user(db_session)

    _, token_hash = generate_invitation_token()
    repo = InvitationRepository(db_session)
    inv = await repo.create(
        organization_id=org.id,
        email="accept@example.com",
        role=MembershipRole.REVIEWER,
        token_hash=token_hash,
        invited_by=user.id,
    )
    await db_session.flush()

    await repo.mark_accepted(inv.id)
    await db_session.flush()

    await db_session.refresh(inv)
    assert inv.status == InvitationStatus.ACCEPTED
    assert inv.accepted_at is not None


@pytest.mark.asyncio
async def test_invitation_no_duplicate_pending(db_session):
    """find_pending_by_org_and_email returns existing pending invitation."""
    org = await _make_org(db_session)
    user = await _make_user(db_session)

    _, token_hash = generate_invitation_token()
    repo = InvitationRepository(db_session)
    await repo.create(
        organization_id=org.id,
        email="dup@example.com",
        role=MembershipRole.REVIEWER,
        token_hash=token_hash,
        invited_by=user.id,
    )
    await db_session.flush()

    pending = await repo.find_pending_by_org_and_email(org.id, "dup@example.com")
    assert pending is not None
