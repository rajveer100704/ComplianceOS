from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.repositories.base import ISessionRepository
from database.models.refresh_token import RefreshToken
from database.models.session_model import SessionModel


class TokenRepository(ISessionRepository):
    """Domain repository for refresh token and session persistence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Refresh Token Methods ---

    async def create_refresh_token(
        self,
        user_id: str,
        token_family: str,
        token_hash: str,
        expires_at: datetime,
        created_by_ip: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token entry."""
        token = RefreshToken(
            user_id=user_id,
            token_family=token_family,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by_ip=created_by_ip,
            device_name=device_name,
            is_revoked=False,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def find_refresh_token_by_hash(
        self, token_hash: str
    ) -> Optional[RefreshToken]:
        """Fetch refresh token by SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_token_used(
        self, token_id: str, replaced_by_hash: Optional[str] = None
    ) -> None:
        """Update last_used_at and mark token replaced during rotation."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(
                last_used_at=now,
                replaced_by_token=replaced_by_hash,
                updated_at=now,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_token_family(self, token_family: str) -> int:
        """Revoke all tokens in a family during token replay detection. Returns count revoked."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_family == token_family,
                RefreshToken.is_revoked.is_(False),
            )
            .values(
                is_revoked=True,
                revoked_at=now,
                updated_at=now,
            )
        )
        result: Any = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount)

    # --- Session Methods (ISessionRepository Implementation) ---

    async def create_session(self, session_entity: SessionModel) -> SessionModel:
        """Persist a new user session."""
        self.session.add(session_entity)
        await self.session.flush()
        return session_entity

    async def find_by_token_hash(self, token_hash: str) -> Optional[SessionModel]:
        """Find session by session token hash."""
        stmt = select(SessionModel).where(
            SessionModel.session_token_hash == token_hash,
            SessionModel.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def touch_activity(self, session_id: str) -> bool:
        """Update last activity timestamp on session."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(last_activity_at=now, updated_at=now)
        )
        result: Any = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount > 0)

    async def revoke_session(self, session_id: str) -> bool:
        """Revoke / soft-delete user session."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(is_deleted=True, deleted_at=now, updated_at=now)
        )
        result: Any = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount > 0)

    async def list_active_by_user(self, user_id: str) -> List[SessionModel]:
        """List all active non-expired sessions for a user."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.is_deleted.is_(False),
                SessionModel.expires_at > now,
            )
            .order_by(SessionModel.last_activity_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
