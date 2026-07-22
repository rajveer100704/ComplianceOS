from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.membership import OrganizationMembership
from database.models.enums import MembershipRole
from database.repositories.base import BaseRepository


class OrganizationMembershipRepository(BaseRepository[OrganizationMembership]):
    """Data access for OrganizationMembership entities."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, OrganizationMembership)

    async def create(
        self,
        *,
        organization_id: str,
        user_id: str,
        role: MembershipRole,
        invited_by: Optional[str] = None,
        joined_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
    ) -> OrganizationMembership:
        """Creates and flushes a new membership record."""
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
            joined_at=joined_at or datetime.now(timezone.utc),
            created_by=created_by,
            updated_by=created_by,
        )
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def find_by_org_and_user(
        self, org_id: str, user_id: str
    ) -> Optional[OrganizationMembership]:
        """Returns the active membership for a user within an organization."""
        result = await self.session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_members(self, org_id: str) -> List[OrganizationMembership]:
        """Returns all active memberships for an organization."""
        result = await self.session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        return list(result.scalars().all())

    async def update_role(
        self,
        membership_id: str,
        new_role: MembershipRole,
        updated_by: Optional[str] = None,
    ) -> Optional[OrganizationMembership]:
        """Updates the role of an existing membership."""
        await self.session.execute(
            update(OrganizationMembership)
            .where(OrganizationMembership.id == membership_id)
            .values(
                role=new_role,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )
        await self.session.flush()
        return await self.session.get(OrganizationMembership, membership_id)

    async def soft_delete(
        self, membership_id: str, deleted_by: Optional[str] = None
    ) -> None:
        """Soft-deletes a membership, effectively removing the user from the org."""
        membership = await self.session.get(OrganizationMembership, membership_id)
        if membership:
            membership.is_deleted = True
            membership.deleted_at = datetime.now(timezone.utc)
            membership.updated_by = deleted_by
            await self.session.flush()

    async def is_member(self, org_id: str, user_id: str) -> bool:
        """Returns True if the user has an active membership in the org."""
        membership = await self.find_by_org_and_user(org_id, user_id)
        return membership is not None

    async def count_owners(self, org_id: str) -> int:
        """Returns the count of active owner memberships (prevent last-owner removal)."""
        result = await self.session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.role == MembershipRole.OWNER,
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        return len(result.scalars().all())

    async def list_members_for_user(self, user_id: str) -> List[OrganizationMembership]:
        """Returns all active memberships for a given user (across all orgs), ordered by created_at."""
        result = await self.session.execute(
            select(OrganizationMembership)
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_deleted.is_(False),
            )
            .order_by(OrganizationMembership.created_at)
        )
        return list(result.scalars().all())
