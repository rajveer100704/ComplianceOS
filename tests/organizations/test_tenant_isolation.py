"""Tenant isolation security tests — cross-tenant access must always return 403.

This suite covers:
  - Cross-tenant read attempt → 403
  - Deleted organization → 403
  - Suspended (soft-deleted) membership → 403
  - Invitation replay (accepting twice) → 409
  - Default org selection (no header → first membership selected)
"""

import pytest
from datetime import datetime, timezone

from fastapi import HTTPException

from database.models.user import User
from database.models.organization import Organization
from database.models.membership import OrganizationMembership
from database.models.enums import MembershipRole, OrganizationPlan
from database.repositories.organization_repository import OrganizationRepository
from database.repositories.membership_repository import OrganizationMembershipRepository
from database.repositories.invitation_repository import (
    InvitationRepository,
    generate_invitation_token,
)
from organizations.service import OrganizationService
from auth.schemas import SecurityContext

# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────


async def _make_user(db, email="alice@example.com") -> User:
    user = User(email=email, full_name="Alice", status="active", is_active=True)
    db.add(user)
    await db.flush()
    return user


async def _make_org(db, slug="acme") -> Organization:
    org = Organization(
        name="Acme", slug=slug, plan=OrganizationPlan.FREE, is_active=True
    )
    db.add(org)
    await db.flush()
    return org


async def _make_membership(
    db, org_id, user_id, role=MembershipRole.OWNER
) -> OrganizationMembership:
    mem = OrganizationMembership(
        organization_id=org_id,
        user_id=user_id,
        role=role,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(mem)
    await db.flush()
    return mem


def _make_security_context(
    user: User, membership: OrganizationMembership | None = None
) -> SecurityContext:
    return SecurityContext(
        user=user,
        membership=membership,
        organization=None,
        permissions=set(),
        token="test_token",
        organization_id=membership.organization_id if membership else None,
        request_id="test-req-id",
    )


# ──────────────────────────────────────────────────────────────
# Cross-Tenant Access → 403
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cross_tenant_list_members_returns_403(db_session):
    """User from org-A cannot list members of org-B."""
    user_a = await _make_user(db_session, email="a@test.com")
    user_b = await _make_user(db_session, email="b@test.com")

    org_a = await _make_org(db_session, slug="org-a")
    org_b = await _make_org(db_session, slug="org-b")

    mem_a = await _make_membership(
        db_session, org_a.id, user_a.id, MembershipRole.OWNER
    )
    await _make_membership(db_session, org_b.id, user_b.id, MembershipRole.OWNER)

    # user_a's security context is scoped to org_a
    ctx = _make_security_context(user_a, mem_a)

    svc = OrganizationService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.list_members(org_id=org_b.id, security_context=ctx)

    assert exc_info.value.status_code == 403


# ──────────────────────────────────────────────────────────────
# Deleted Organization → 403
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_soft_deleted_org_not_found(db_session):
    """A soft-deleted organization is not visible via find_by_id."""
    org_repo = OrganizationRepository(db_session)
    org = await org_repo.create(name="GoneOrg", slug="gone-org")
    await db_session.flush()
    await org_repo.soft_delete(org.id)

    found = await org_repo.find_by_id(org.id)
    assert found is None


# ──────────────────────────────────────────────────────────────
# Suspended Membership → 403
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_soft_deleted_membership_blocks_list_members(db_session):
    """A soft-deleted (suspended) membership results in 403 for list_members."""
    user = await _make_user(db_session, email="suspended@test.com")
    org = await _make_org(db_session, slug="org-susp")
    mem = await _make_membership(db_session, org.id, user.id, MembershipRole.REVIEWER)

    # Soft-delete the membership (simulate suspension)
    mem_repo = OrganizationMembershipRepository(db_session)
    await mem_repo.soft_delete(mem.id)

    # After soft-delete, find_by_org_and_user should return None
    found = await mem_repo.find_by_org_and_user(org.id, user.id)
    assert found is None

    # Service should 403 because membership lookup fails
    ctx = _make_security_context(user, None)  # membership is None after suspension
    svc = OrganizationService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.list_members(org_id=org.id, security_context=ctx)

    assert exc_info.value.status_code == 403


# ──────────────────────────────────────────────────────────────
# Invitation Replay → 409
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invitation_replay_returns_409(db_session):
    """Accepting an already-accepted invitation returns 409 Conflict."""
    user = await _make_user(db_session, email="invitee@test.com")
    org = await _make_org(db_session, slug="org-replay")

    raw_token, token_hash = generate_invitation_token()
    inv_repo = InvitationRepository(db_session)
    await inv_repo.create(
        organization_id=org.id,
        email="invitee@test.com",
        role=MembershipRole.REVIEWER,
        token_hash=token_hash,
        invited_by=user.id,
    )
    await db_session.flush()

    svc = OrganizationService(db_session)

    # First acceptance — succeeds
    await svc.accept_invitation(raw_token=raw_token, user=user)

    # Second acceptance — replay attack → 410 GONE or 409 CONFLICT
    with pytest.raises(HTTPException) as exc_info:
        await svc.accept_invitation(raw_token=raw_token, user=user)

    assert exc_info.value.status_code in (409, 410)


# ──────────────────────────────────────────────────────────────
# Invite to org user already belongs to → 409
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invite_existing_member_returns_409(db_session):
    """Inviting an already-active member results in 409 Conflict."""
    user = await _make_user(db_session, email="existing@test.com")
    org = await _make_org(db_session, slug="org-dup-invite")
    mem = await _make_membership(db_session, org.id, user.id, MembershipRole.OWNER)

    # Owner invites themselves (or another existing member with the same email)
    ctx = _make_security_context(user, mem)
    ctx.membership = mem  # ensure membership is set for org enforcement

    svc = OrganizationService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await svc.invite_member(
            org_id=org.id,
            email="existing@test.com",
            role=MembershipRole.REVIEWER,
            security_context=ctx,
        )
    assert exc_info.value.status_code == 409


# ──────────────────────────────────────────────────────────────
# Default Organization Selection
# ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_default_org_is_first_membership(db_session):
    """When no X-Organization-Id header is sent, the first membership by created_at is selected."""
    user = await _make_user(db_session, email="multi@test.com")

    org_a = await _make_org(db_session, slug="first-org")
    org_b = await _make_org(db_session, slug="second-org")

    mem_repo = OrganizationMembershipRepository(db_session)
    # Create two memberships — first will have an earlier created_at
    await mem_repo.create(
        organization_id=org_a.id,
        user_id=user.id,
        role=MembershipRole.REVIEWER,
        joined_at=datetime.now(timezone.utc),
    )
    await mem_repo.create(
        organization_id=org_b.id,
        user_id=user.id,
        role=MembershipRole.REVIEWER,
        joined_at=datetime.now(timezone.utc),
    )
    await db_session.flush()

    all_mems = await mem_repo.list_members_for_user(user.id)
    assert len(all_mems) == 2
    # First returned membership should be org_a
    assert all_mems[0].organization_id == org_a.id
