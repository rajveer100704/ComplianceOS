from database.repositories.base import BaseRepository
from database.models.audit import AuditLogModel


class ReceiptRepository(BaseRepository[AuditLogModel]):
    """Repository mapping enterprise audit log activities."""

    def __init__(self, session):
        super().__init__(session, AuditLogModel)
