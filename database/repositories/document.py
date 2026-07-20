from database.repositories.base import BaseRepository
from database.models.document import DocumentModel

class DocumentRepository(BaseRepository[DocumentModel]):
    """Repository mapping uploaded document source files lookups."""

    def __init__(self, session):
        super().__init__(session, DocumentModel)
