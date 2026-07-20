from database.repositories.base import BaseRepository
from database.models.run import RunModel

class RunRepository(BaseRepository[RunModel]):
    """Repository mapping run versions and pipeline validation logs."""

    def __init__(self, session):
        super().__init__(session, RunModel)
