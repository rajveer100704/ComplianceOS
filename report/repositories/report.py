from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.report import ReportModel

class ReportRepository(BaseRepository[ReportModel]):
    """Repository mapping report persistence operations."""

    def __init__(self, session):
        super().__init__(session, ReportModel)

    async def get_by_request(self, request_id: int) -> List[ReportModel]:
        """Fetches all reports generated for a specific request ordered by version."""
        stmt = (
            select(ReportModel)
            .where(ReportModel.request_id == request_id, ReportModel.is_deleted == False)
            .order_by(ReportModel.version.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_latest_version(self, request_id: int) -> int:
        """Returns the highest report version number recorded for a request."""
        stmt = select(func.max(ReportModel.version)).where(
            ReportModel.request_id == request_id,
            ReportModel.is_deleted == False
        )
        res = await self.session.execute(stmt)
        val = res.scalar()
        return val if val is not None else 0

    async def get_by_version(self, request_id: int, version: int) -> Optional[ReportModel]:
        """Fetches a specific version of a report for a request."""
        stmt = select(ReportModel).where(
            ReportModel.request_id == request_id,
            ReportModel.version == version,
            ReportModel.is_deleted == False
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
