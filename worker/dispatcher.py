import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select

from database.services.unit_of_work import UnitOfWork
from database.models.outbox import OutboxEventModel

logger = logging.getLogger("outbox_dispatcher")


class OutboxDispatcher:
    """Dispatches transaction outbox events to background worker tasks."""

    def __init__(self, queue_backend, interval_sec: float = 2.0):
        self.queue_backend = queue_backend
        self.interval_sec = interval_sec
        self._task = None
        self.running = False

    async def start(self):
        self.running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("OutboxDispatcher event loop started.")

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
                await self.dispatch_events()
            except Exception as e:
                logger.error(f"Error in outbox dispatcher sweep: {e}")
            await asyncio.sleep(self.interval_sec)

    async def dispatch_events(self):
        """Finds unprocessed outbox events, enqueues worker tasks, and marks events processed."""
        async with UnitOfWork() as uow:
            stmt = (
                select(OutboxEventModel)
                .where(OutboxEventModel.processed == False)
                .order_by(OutboxEventModel.id)
            )
            res = await uow.session.execute(stmt)
            events = res.scalars().all()

            for event in events:
                logger.info(f"Processing outbox event {event.id} ({event.event_type})")

                try:
                    if event.event_type == "document_uploaded":
                        payload = event.payload
                        source_type = payload.get("source_type", "text")

                        if source_type == "pdf":
                            import uuid

                            unique_id = str(uuid.uuid4())
                            task_id = f"task-{unique_id}"

                            from worker.state import TaskStateManager

                            await TaskStateManager.create_task(
                                task_id, "parse_and_index_document_task"
                            )

                            temp_dir = (
                                Path(__file__).parent.parent / "storage" / "uploads"
                            )
                            temp_path = temp_dir / f"{payload['filename']}"

                            await self.queue_backend.enqueue(
                                task_id,
                                "parse_and_index_document_task",
                                task_id=task_id,
                                request_id=payload["request_id"],
                                doc_id=payload["document_id"],
                                file_path=str(temp_path),
                            )

                    event.processed = True
                    event.processed_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(f"Failed to dispatch outbox event {event.id}: {e}")

            await uow.commit()
