from database.repositories.base import BaseRepository
from database.models.claim import ClaimModel

class ClaimRepository(BaseRepository[ClaimModel]):
    """Repository mapping claim-specific review decisions and comments."""

    def __init__(self, session):
        super().__init__(session, ClaimModel)
