from typing import List
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.report import ReportActivityLogModel


class ReportActivityLogRepository(BaseRepository[ReportActivityLogModel]):
    """Repository mapping report activity logs and audit timeline operations."""

    def __init__(self, session):
        super().__init__(session, ReportActivityLogModel)

    async def get_timeline(self, report_id: int) -> List[ReportActivityLogModel]:
        """Fetches all timeline logs for a report ordered by creation date."""
        stmt = (
            select(ReportActivityLogModel)
            .where(
                ReportActivityLogModel.report_id == report_id,
                ReportActivityLogModel.is_deleted == False,
            )
            .order_by(ReportActivityLogModel.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
