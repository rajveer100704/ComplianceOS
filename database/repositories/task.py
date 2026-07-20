from database.repositories.base import BaseRepository
from database.models.task import TaskModel

class TaskRepository(BaseRepository[TaskModel]):
    """Repository handling database operations for background tasks."""
    def __init__(self, session):
        super().__init__(session, TaskModel)
