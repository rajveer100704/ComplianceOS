import hashlib
import secrets
from typing import Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.invitation import Invitation
from database.models.enums import MembershipRole, InvitationStatus
from database.repositories.base import BaseRepository


# Invitation token validity window
_INVITATION_TTL_HOURS = 72


def generate_invitation_token() -> tuple[str, str]:
    """Generates a cryptographically secure invitation token and its SHA-256 hash.

    Returns:
        (raw_token, token_hash) — store only token_hash; return raw_token to caller.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


class InvitationRepository(BaseRepository[Invitation]):
    """Data access for Invitation entities."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Invitation)

    async def create(
        self,
        *,
        organization_id: str,
        email: str,
        role: MembershipRole,
        token_hash: str,
        invited_by: str,
        ttl_hours: int = _INVITATION_TTL_HOURS,
        created_by: Optional[str] = None,
    ) -> Invitation:
        """Creates and flushes a new pending invitation."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        invitation = Invitation(
            organization_id=organization_id,
            email=email,
            role=role,
            token_hash=token_hash,
            expires_at=expires_at,
            status=InvitationStatus.PENDING,
            invited_by=invited_by,
            created_by=created_by,
            updated_by=created_by,
        )
        self.session.add(invitation)
        await self.session.flush()
        return invitation

    async def find_by_token_hash(self, token_hash: str) -> Optional[Invitation]:
        """Returns a non-deleted invitation matching the given SHA-256 token hash."""
        result = await self.session.execute(
            select(Invitation).where(
                Invitation.token_hash == token_hash,
                Invitation.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def find_pending_by_org_and_email(
        self, org_id: str, email: str
    ) -> Optional[Invitation]:
        """Returns an active pending invitation for an email in an org (to prevent duplicates)."""
        result = await self.session.execute(
            select(Invitation).where(
                Invitation.organization_id == org_id,
                Invitation.email == email,
                Invitation.status == InvitationStatus.PENDING,
                Invitation.is_deleted.is_(False),
                Invitation.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def mark_accepted(self, invitation_id: str) -> None:
        """Marks an invitation as accepted with the current timestamp."""
        now = datetime.now(timezone.utc)
        await self.session.execute(
            update(Invitation)
            .where(Invitation.id == invitation_id)
            .values(
                status=InvitationStatus.ACCEPTED,
                accepted_at=now,
                updated_at=now,
            )
        )
        await self.session.flush()

    async def mark_revoked(self, invitation_id: str) -> None:
        """Revokes an invitation, preventing further use."""
        await self.session.execute(
            update(Invitation)
            .where(Invitation.id == invitation_id)
            .values(
                status=InvitationStatus.REVOKED,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.flush()

    async def expire_stale_invitations(self) -> int:
        """Marks all past-expiry pending invitations as expired. Returns count."""
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            update(Invitation)
            .where(
                Invitation.status == InvitationStatus.PENDING,
                Invitation.expires_at <= now,
                Invitation.is_deleted.is_(False),
            )
            .values(status=InvitationStatus.EXPIRED, updated_at=now)
        )
        await self.session.flush()
        return result.rowcount
