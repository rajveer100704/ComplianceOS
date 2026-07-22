"""Unit tests for Organization, OrganizationMembership, Team, and Invitation ORM models."""
import pytest
from datetime import datetime, timezone, timedelta

from database.models.organization import Organization
from database.models.membership import OrganizationMembership
from database.models.team import Team
from database.models.invitation import Invitation
from database.models.enums import (
    MembershipRole,
    InvitationStatus,
    OrganizationPlan,
)


class TestOrganizationModel:
    @pytest.mark.asyncio
    async def test_organization_defaults(self, db_session):
        """Organization defaults plan=FREE and is_active=True."""
        org = Organization(name="Acme Corp", slug="acme-corp")
        db_session.add(org)
        await db_session.flush()
        assert org.plan == OrganizationPlan.FREE or org.plan == "free"
        assert org.is_active is True

    def test_organization_slug_max_length(self):
        """Slug is bounded by DB column (255 chars)."""
        org = Organization(name="Test", slug="a" * 255)
        assert len(org.slug) == 255

    def test_organization_plan_enum_values(self):
        """OrganizationPlan enum contains all expected tiers."""
        plans = {p.value for p in OrganizationPlan}
        assert plans == {"free", "pro", "business", "enterprise"}


class TestOrganizationMembershipModel:
    @pytest.mark.asyncio
    async def test_membership_default_role(self, db_session):
        """Default role is REVIEWER."""
        org = Organization(name="Org 1", slug="org-1")
        db_session.add(org)
        await db_session.flush()

        m = OrganizationMembership(
            organization_id=org.id,
            user_id="user-1",
        )
        db_session.add(m)
        await db_session.flush()
        assert m.role == MembershipRole.REVIEWER or m.role == "reviewer"

    def test_membership_role_enum_values(self):
        """MembershipRole contains all expected values."""
        roles = {r.value for r in MembershipRole}
        assert roles == {"owner", "admin", "lead_reviewer", "reviewer", "auditor"}

    def test_membership_joined_at_nullable(self):
        """joined_at is nullable for pending invitations."""
        m = OrganizationMembership(
            organization_id="org-1",
            user_id="user-1",
            role=MembershipRole.REVIEWER,
        )
        assert m.joined_at is None


class TestTeamModel:
    def test_team_fields(self):
        """Team model carries org scope, name, slug, and description."""
        team = Team(
            organization_id="org-1",
            name="Engineering",
            slug="engineering",
            description="Core engineering team",
        )
        assert team.organization_id == "org-1"
        assert team.slug == "engineering"
        assert team.description == "Core engineering team"


class TestInvitationModel:
    @pytest.mark.asyncio
    async def test_invitation_default_status(self, db_session):
        """Default invitation status is PENDING."""
        org = Organization(name="Org Inv", slug="org-inv")
        db_session.add(org)
        await db_session.flush()

        inv = Invitation(
            organization_id=org.id,
            email="alice@example.com",
            role=MembershipRole.REVIEWER,
            token_hash="abc123",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
            invited_by="user-1",
        )
        db_session.add(inv)
        await db_session.flush()
        assert inv.status == InvitationStatus.PENDING or inv.status == "pending"

    def test_invitation_status_enum_values(self):
        """InvitationStatus contains all expected lifecycle states."""
        states = {s.value for s in InvitationStatus}
        assert states == {"pending", "accepted", "expired", "revoked"}

    def test_invitation_accepted_at_nullable(self):
        """accepted_at is nullable for pending invitations."""
        inv = Invitation(
            organization_id="org-1",
            email="bob@example.com",
            role=MembershipRole.AUDITOR,
            token_hash="xyz789",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            invited_by="user-1",
        )
        assert inv.accepted_at is None
