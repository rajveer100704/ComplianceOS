from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from auth.repositories.user_repository import UserRepository


class AuthService:
    """Service interface for OAuth authentication workflows (Sprint 2 implementation)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def handle_google_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Placeholder for Google OAuth callback processing (Sprint 2)."""
        raise NotImplementedError(
            "Google OAuth callback handling will be implemented in Sprint 2."
        )

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Placeholder for retrieving authenticated user profile (Sprint 2)."""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "status": user.status.value,
        }
