from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from auth.repositories.token_repository import TokenRepository


class SessionService:
    """Service interface for session lifecycle management (Sprint 2 implementation)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.token_repo = TokenRepository(session)

    async def validate_session(self, token_hash: str) -> Optional[str]:
        """Placeholder for active session validation (Sprint 2)."""
        session_obj = await self.token_repo.find_by_token_hash(token_hash)
        if not session_obj or session_obj.is_deleted:
            return None
        return session_obj.user_id
