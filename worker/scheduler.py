import logging
import asyncio
from datetime import datetime, timezone, timedelta
from database.services.unit_of_work import UnitOfWork
from database.models.task import TaskModel
from worker.state import TaskStateManager

logger = logging.getLogger("worker_scheduler")

class TaskScheduler:
    """Orchestrates periodic sweeps for stuck tasks (visibility timeout recovery)."""

    def __init__(self, queue_backend, visibility_timeout_sec: int = 300, interval_sec: int = 60):
        self.queue_backend = queue_backend
        self.visibility_timeout_sec = visibility_timeout_sec
        self.interval_sec = interval_sec
        self._task = None
        self.running = False

    async def start(self):
        self.running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("TaskScheduler scheduler sweep loop started.")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        while self.running:
            try:
                await self.recover_stuck_tasks()
            except Exception as e:
                logger.error(f"Error recovering stuck tasks in scheduler: {e}")
            await asyncio.sleep(self.interval_sec)

    async def recover_stuck_tasks(self):
        """Finds running/claimed tasks older than the visibility timeout and re-queues them."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.visibility_timeout_sec)

        async with UnitOfWork() as uow:
            from sqlalchemy import select
            stmt = select(TaskModel).where(
                TaskModel.status.in_(["RUNNING", "CLAIMED"]),
                TaskModel.updated_at < cutoff_time
            )
            res = await uow.session.execute(stmt)
            stuck_tasks = res.scalars().all()

            for task in stuck_tasks:
                logger.warning(f"Task {task.id} ({task.name}) has timed out. Reclaiming...")

                if task.retries >= task.max_retries:
                    task.status = "DEAD_LETTER"
                    task.error = f"Visibility timeout exceeded. Max retries ({task.max_retries}) reached."
                    logger.error(f"Task {task.id} routed to Dead Letter Queue (DLQ).")
                else:
                    task.status = "QUEUED"
                    task.retries += 1
                    task.updated_at = datetime.now(timezone.utc)
                    await self.queue_backend.enqueue(task.id, task.name)
                    logger.info(f"Task {task.id} re-enqueued for retry attempt {task.retries}.")

            await uow.commit()
