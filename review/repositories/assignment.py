from typing import List, Optional
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.review import ReviewAssignmentModel


class AssignmentRepository(BaseRepository[ReviewAssignmentModel]):
    """Repository mapping reviewer assignment history query operations."""

    def __init__(self, session):
        super().__init__(session, ReviewAssignmentModel)

    async def get_history(self, request_id: int) -> List[ReviewAssignmentModel]:
        """Fetches all reviewer assignment history logs for a request."""
        stmt = (
            select(ReviewAssignmentModel)
            .where(
                ReviewAssignmentModel.request_id == request_id,
                ReviewAssignmentModel.is_deleted == False,
            )
            .order_by(ReviewAssignmentModel.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_active_assignment(
        self, request_id: int
    ) -> Optional[ReviewAssignmentModel]:
        """Fetches the current active assignment (where unassigned_at is not set)."""
        stmt = select(ReviewAssignmentModel).where(
            ReviewAssignmentModel.request_id == request_id,
            ReviewAssignmentModel.unassigned_at == None,
            ReviewAssignmentModel.is_deleted == False,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
