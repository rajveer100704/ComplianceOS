from database.repositories.base import BaseRepository
from database.models.requirement import RequirementModel


class RequirementRepository(BaseRepository[RequirementModel]):
    """Repository mapping seeded regulation requirements corpus lookups."""

    def __init__(self, session):
        super().__init__(session, RequirementModel)
