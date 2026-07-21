from typing import List
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.review import PinnedEvidenceModel


class EvidenceRepository(BaseRepository[PinnedEvidenceModel]):
    """Repository mapping pinned evidence operations for claims."""

    def __init__(self, session):
        super().__init__(session, PinnedEvidenceModel)

    async def get_by_claim(self, claim_id: int) -> List[PinnedEvidenceModel]:
        """Fetches all pinned evidence records for a specific claim."""
        stmt = select(PinnedEvidenceModel).where(
            PinnedEvidenceModel.claim_id == claim_id,
            PinnedEvidenceModel.is_deleted == False,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_claim_and_chunk(
        self, claim_id: int, chunk_id: str
    ) -> List[PinnedEvidenceModel]:
        """Fetches pinned evidence records matching both claim and chunk identifiers."""
        stmt = select(PinnedEvidenceModel).where(
            PinnedEvidenceModel.claim_id == claim_id,
            PinnedEvidenceModel.chunk_id == chunk_id,
            PinnedEvidenceModel.is_deleted == False,
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
