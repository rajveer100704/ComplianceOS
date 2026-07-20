from typing import List
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.review import ReviewActivityLogModel

class ActivityLogRepository(BaseRepository[ReviewActivityLogModel]):
    """Repository mapping review activity logs and audit timeline operations."""

    def __init__(self, session):
        super().__init__(session, ReviewActivityLogModel)

    async def get_timeline(self, request_id: int) -> List[ReviewActivityLogModel]:
        """Fetches all timeline logs for a request ordered by creation date."""
        stmt = (
            select(ReviewActivityLogModel)
            .where(ReviewActivityLogModel.request_id == request_id, ReviewActivityLogModel.is_deleted == False)
            .order_by(ReviewActivityLogModel.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
