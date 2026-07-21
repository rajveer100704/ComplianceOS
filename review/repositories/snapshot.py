from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.future import select
from database.repositories.base import BaseRepository
from database.models.review import ReviewSnapshotModel


class SnapshotRepository(BaseRepository[ReviewSnapshotModel]):
    """Repository mapping review snapshot persistence operations."""

    def __init__(self, session):
        super().__init__(session, ReviewSnapshotModel)

    async def get_latest_version(self, request_id: int) -> int:
        """Returns the highest snapshot version number recorded for a request."""
        stmt = select(func.max(ReviewSnapshotModel.version)).where(
            ReviewSnapshotModel.request_id == request_id,
            ReviewSnapshotModel.is_deleted == False,
        )
        res = await self.session.execute(stmt)
        val = res.scalar()
        return val if val is not None else 0

    async def get_by_version(
        self, request_id: int, version: int
    ) -> Optional[ReviewSnapshotModel]:
        """Fetches the snapshot corresponding to a specific version number."""
        stmt = select(ReviewSnapshotModel).where(
            ReviewSnapshotModel.request_id == request_id,
            ReviewSnapshotModel.version == version,
            ReviewSnapshotModel.is_deleted == False,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_all_for_request(self, request_id: int) -> List[ReviewSnapshotModel]:
        """Fetches all snapshots stored for a specific request ordered by version."""
        stmt = (
            select(ReviewSnapshotModel)
            .where(
                ReviewSnapshotModel.request_id == request_id,
                ReviewSnapshotModel.is_deleted == False,
            )
            .order_by(ReviewSnapshotModel.version.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
