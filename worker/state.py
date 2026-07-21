import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from database.services.unit_of_work import UnitOfWork
from database.models.task import TaskModel

logger = logging.getLogger("worker_state")


class TaskStateManager:
    """Manages persistent task state lifecycle tracking across Database and Queue backends."""

    @staticmethod
    async def create_task(task_id: str, name: str, max_retries: int = 3) -> None:
        """Initializes a new task tracking record in the database."""
        async with UnitOfWork() as uow:
            task = TaskModel(
                id=task_id,
                name=name,
                status="QUEUED",
                retries=0,
                max_retries=max_retries,
            )
            await uow.tasks.add(task)
            await uow.commit()
        logger.info(f"Task {task_id} ({name}) initialized in database.")

    @staticmethod
    async def update_task_status(
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        increment_retries: bool = False,
    ) -> None:
        """Updates task state, results, errors, and retries count."""
        async with UnitOfWork() as uow:
            task = await uow.tasks.get(task_id)
            if not task:
                task = TaskModel(id=task_id, name="unknown", status=status)
                await uow.tasks.add(task)

            task.status = status
            if error is not None:
                task.error = error
            if result is not None:
                if not isinstance(result, str):
                    task.result = json.dumps(result)
                else:
                    task.result = result
            if increment_retries:
                task.retries += 1

            task.updated_at = datetime.now(timezone.utc)
            await uow.commit()
        logger.info(f"Task {task_id} updated to status {status}.")

    @staticmethod
    async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves task state details."""
        async with UnitOfWork() as uow:
            task = await uow.tasks.get(task_id)
            if not task:
                return None
            try:
                res_data = json.loads(task.result) if task.result else None
            except Exception:
                res_data = task.result
            return {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "retries": task.retries,
                "max_retries": task.max_retries,
                "error": task.error,
                "result": res_data,
                "created_at": task.created_at.isoformat() + "Z",
                "updated_at": task.updated_at.isoformat() + "Z",
            }
