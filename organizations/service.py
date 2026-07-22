import logging
import re
from typing import Optional
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from database.models.organization import Organization
from database.models.membership import OrganizationMembership
from database.models.invitation import Invitation
from database.models.user import User
from database.models.enums import MembershipRole, InvitationStatus, OrganizationPlan
from database.repositories.organization_repository import OrganizationRepository
from database.repositories.membership_repository import OrganizationMembershipRepository
from database.repositories.invitation_repository import (
    InvitationRepository,
    generate_invitation_token,
)
from database.events import EventPublisher
from auth.schemas import SecurityContext
from organizations import events as ev

logger = logging.getLogger("complianceos.organizations.service")


def _slugify(text: str) -> str:
    """Converts a display name to a URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


class OrganizationService:
    """Business logic for organization creation, membership management, and invitations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._org_repo = OrganizationRepository(db)
        self._mem_repo = OrganizationMembershipRepository(db)
        self._inv_repo = InvitationRepository(db)

    # ──────────────────────────────────────────────────────────────
    # Organization
    # ──────────────────────────────────────────────────────────────

    async def create_organization(
        self,
        *,
        name: str,
        slug: Optional[str] = None,
        plan: OrganizationPlan = OrganizationPlan.FREE,
        creator: User,
    ) -> tuple[Organization, OrganizationMembership]:
        """Creates a new organization and assigns the creator as OWNER.

        Returns:
            (organization, membership) tuple.

        Raises:
            HTTPException 409 — if slug is already taken.
        """
        resolved_slug = slug or _slugify(name)

        # Ensure slug uniqueness
        if await self._org_repo.slug_exists(resolved_slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization slug '{resolved_slug}' is already taken.",
            )

        org = await self._org_repo.create(
            name=name,
            slug=resolved_slug,
            plan=plan.value,
            created_by=creator.id,
        )

        membership = await self._mem_repo.create(
            organization_id=org.id,
            user_id=creator.id,
            role=MembershipRole.OWNER,
            joined_at=datetime.now(timezone.utc),
            created_by=creator.id,
        )

        await EventPublisher.publish_event(
            ev.ORG_CREATED,
            {
                "organization_id": org.id,
                "name": org.name,
                "slug": org.slug,
                "created_by": creator.id,
            },
            session=self._db,
        )

        logger.info(
            "Organization created: id=%s slug=%s by user=%s",
            org.id,
            org.slug,
            creator.id,
        )
        return org, membership

    async def list_user_organizations(self, user_id: str) -> list[dict]:
        """Returns all organizations the user is a member of, with their role."""
        orgs = await self._org_repo.list_for_user(user_id)
        result = []
        for org in orgs:
            membership = await self._mem_repo.find_by_org_and_user(org.id, user_id)
            result.append(
                {
                    "organization": org,
                    "membership": membership,
                }
            )
        return result

    # ──────────────────────────────────────────────────────────────
    # Invitations
    # ──────────────────────────────────────────────────────────────

    async def invite_member(
        self,
        *,
        org_id: str,
        email: str,
        role: MembershipRole,
        security_context: SecurityContext,
    ) -> tuple[Invitation, Optional[str]]:
        """Creates an invitation for a new member.

        Enforces:
          - Caller must be OWNER or ADMIN of the org.
          - Cannot invite an existing member.
          - Cannot create a duplicate pending invitation.

        Returns:
            (invitation, raw_token) where raw_token is only populated in development.

        Raises:
            HTTPException 403 — if caller lacks permission.
            HTTPException 409 — if member already exists or pending invitation exists.
        """
        self._enforce_admin_or_owner(security_context, org_id)

        # Check caller is actually in this org
        caller_membership = await self._mem_repo.find_by_org_and_user(
            org_id, security_context.user.id
        )
        if not caller_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization.",
            )

        # Prevent duplicate active membership
        from auth.repositories.user_repository import UserRepository

        user_repo = UserRepository(self._db)
        existing_user = await user_repo.find_by_email(email)
        if existing_user:
            existing_membership = await self._mem_repo.find_by_org_and_user(
                org_id, existing_user.id
            )
            if existing_membership:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This user is already a member of the organization.",
                )

        # Prevent duplicate pending invitation
        existing_inv = await self._inv_repo.find_pending_by_org_and_email(org_id, email)
        if existing_inv:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation already exists for this email address.",
            )

        raw_token, token_hash = generate_invitation_token()

        invitation = await self._inv_repo.create(
            organization_id=org_id,
            email=email,
            role=role,
            token_hash=token_hash,
            invited_by=security_context.user.id,
            created_by=security_context.user.id,
        )

        await EventPublisher.publish_event(
            ev.MEMBER_INVITED,
            {
                "invitation_id": invitation.id,
                "organization_id": org_id,
                "email": email,
                "role": role.value,
                "invited_by": security_context.user.id,
            },
            session=self._db,
        )

        # Only expose raw token in development mode (for testing)
        debug_token = raw_token if settings.ENVIRONMENT == "development" else None

        return invitation, debug_token

    async def accept_invitation(
        self,
        *,
        raw_token: str,
        user: User,
    ) -> OrganizationMembership:
        """Verifies an invitation token and creates an org membership.

        Raises:
            HTTPException 404 — token not found.
            HTTPException 410 — token expired or already used.
            HTTPException 409 — user already a member (invitation replay).
        """
        import hashlib

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        invitation = await self._inv_repo.find_by_token_hash(token_hash)

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found.",
            )

        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Invitation is no longer valid (status: {invitation.status.value}).",
            )

        if datetime.now(timezone.utc) > invitation.expires_at.replace(
            tzinfo=timezone.utc
        ):
            await self._inv_repo.mark_revoked(invitation.id)
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invitation has expired.",
            )

        # Check for replay (user already a member)
        existing = await self._mem_repo.find_by_org_and_user(
            invitation.organization_id, user.id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member of this organization.",
            )

        membership = await self._mem_repo.create(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=invitation.role,
            invited_by=invitation.invited_by,
            joined_at=datetime.now(timezone.utc),
            created_by=user.id,
        )

        await self._inv_repo.mark_accepted(invitation.id)

        await EventPublisher.publish_event(
            ev.MEMBER_JOINED,
            {
                "organization_id": invitation.organization_id,
                "user_id": user.id,
                "role": invitation.role.value,
                "invitation_id": invitation.id,
            },
            session=self._db,
        )

        return membership

    # ──────────────────────────────────────────────────────────────
    # Members
    # ──────────────────────────────────────────────────────────────

    async def list_members(
        self,
        *,
        org_id: str,
        security_context: SecurityContext,
    ) -> list[OrganizationMembership]:
        """Lists all active members of an organization.

        Raises:
            HTTPException 403 — caller is not a member of the org.
        """
        caller_membership = await self._mem_repo.find_by_org_and_user(
            org_id, security_context.user.id
        )
        if not caller_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization.",
            )
        return await self._mem_repo.list_members(org_id)

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    def _enforce_admin_or_owner(
        self, security_context: SecurityContext, org_id: str
    ) -> None:
        """Raises 403 if the caller's membership role does not permit admin actions."""
        membership = security_context.membership
        if not membership or membership.organization_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization.",
            )
        if membership.role not in (MembershipRole.OWNER, MembershipRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization Owners and Admins can perform this action.",
            )
