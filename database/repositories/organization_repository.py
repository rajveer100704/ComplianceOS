from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.organization import Organization
from database.models.membership import OrganizationMembership
from database.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Data access for Organization entities, auto-scoped via security context."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Organization)

    async def create(
        self,
        *,
        name: str,
        slug: str,
        plan: str = "free",
        created_by: Optional[str] = None,
    ) -> Organization:
        """Creates and persists a new Organization."""
        org = Organization(
            name=name,
            slug=slug,
            plan=plan,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )
        self.session.add(org)
        await self.session.flush()
        return org

    async def find_by_id(self, org_id: str) -> Optional[Organization]:
        """Returns an active Organization by primary key."""
        result = await self.session.execute(
            select(Organization).where(
                Organization.id == org_id,
                Organization.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def find_by_slug(self, slug: str) -> Optional[Organization]:
        """Returns an active Organization by unique slug."""
        result = await self.session.execute(
            select(Organization).where(
                Organization.slug == slug,
                Organization.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> List[Organization]:
        """Returns all organizations where the user has an active membership."""
        result = await self.session.execute(
            select(Organization)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Organization.id,
            )
            .where(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_deleted.is_(False),
                Organization.is_deleted.is_(False),
                Organization.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def soft_delete(self, org_id: str) -> None:
        """Soft-deletes an organization by ID."""
        org = await self.find_by_id(org_id)
        if org:
            org.is_deleted = True
            org.is_active = False
            org.deleted_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def slug_exists(self, slug: str) -> bool:
        """Returns True if a slug is already taken (active or deleted)."""
        result = await self.session.execute(
            select(Organization.id).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none() is not None
