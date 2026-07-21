from database.repositories.base import BaseRepository
from database.models.request import RequestModel


class RequestRepository(BaseRepository[RequestModel]):
    """Repository mapping request-specific database lookups."""

    def __init__(self, session):
        super().__init__(session, RequestModel)
