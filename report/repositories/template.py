from typing import Optional
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.report import ReportTemplateModel

class TemplateRepository(BaseRepository[ReportTemplateModel]):
    """Repository mapping report template query operations."""

    def __init__(self, session):
        super().__init__(session, ReportTemplateModel)

    async def get_by_name(self, name: str) -> Optional[ReportTemplateModel]:
        """Fetches a report template by its name."""
        stmt = (
            select(ReportTemplateModel)
            .where(
                ReportTemplateModel.name == name,
                ReportTemplateModel.is_deleted == False
            )
            .order_by(ReportTemplateModel.id.desc())
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()
