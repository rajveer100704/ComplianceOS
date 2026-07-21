from typing import List
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.review import ClaimCommentModel


class CommentRepository(BaseRepository[ClaimCommentModel]):
    """Repository mapping claim threaded comment operations."""

    def __init__(self, session):
        super().__init__(session, ClaimCommentModel)

    async def get_by_claim(self, claim_id: int) -> List[ClaimCommentModel]:
        """Fetches all comments for a specific claim ordered by creation date."""
        stmt = (
            select(ClaimCommentModel)
            .where(
                ClaimCommentModel.claim_id == claim_id,
                ClaimCommentModel.is_deleted == False,
            )
            .order_by(ClaimCommentModel.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
