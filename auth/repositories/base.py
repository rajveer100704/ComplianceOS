from abc import ABC, abstractmethod
from typing import Optional, List
from database.models.session_model import SessionModel


class ISessionRepository(ABC):
    """Abstract interface for session storage (PostgreSQL / Redis ready)."""

    @abstractmethod
    async def create_session(self, session: SessionModel) -> SessionModel:
        pass

    @abstractmethod
    async def find_by_token_hash(self, token_hash: str) -> Optional[SessionModel]:
        pass

    @abstractmethod
    async def touch_activity(self, session_id: str) -> bool:
        pass

    @abstractmethod
    async def revoke_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    async def list_active_by_user(self, user_id: str) -> List[SessionModel]:
        pass
