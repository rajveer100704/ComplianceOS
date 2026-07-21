from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from auth.repositories.token_repository import TokenRepository


class TokenService:
    """Service interface for RS256 JWT signing and refresh token rotation (Sprint 2 implementation)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.token_repo = TokenRepository(session)

    async def issue_tokens_for_user(self, user_id: str, role: str) -> Dict[str, Any]:
        """Placeholder for issuing RS256 access and refresh tokens (Sprint 2)."""
        raise NotImplementedError("JWT token issuance will be implemented in Sprint 2.")

    async def refresh_access_token(self, refresh_token_raw: str) -> Dict[str, Any]:
        """Placeholder for refresh token rotation and replay detection (Sprint 2)."""
        raise NotImplementedError(
            "Refresh token rotation will be implemented in Sprint 2."
        )
