from typing import List
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.report import ReportCitationModel


class CitationRepository(BaseRepository[ReportCitationModel]):
    """Repository mapping report finding citations operations."""

    def __init__(self, session):
        super().__init__(session, ReportCitationModel)

    async def get_by_finding(self, finding_id: int) -> List[ReportCitationModel]:
        """Fetches all citation mappings associated with a specific finding."""
        stmt = select(ReportCitationModel).where(
            ReportCitationModel.finding_id == finding_id,
            ReportCitationModel.is_deleted == False,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
