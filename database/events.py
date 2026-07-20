from typing import Dict, Any
from database.models.outbox import OutboxEventModel
from database.services.unit_of_work import UnitOfWork

class EventPublisher:
    """Enqueues events in the outbox table for reliable background execution."""

    @staticmethod
    async def publish_event(event_type: str, payload: Dict[str, Any]) -> None:
        async with UnitOfWork() as uow:
            event = OutboxEventModel(event_type=event_type, payload=payload)
            uow.session.add(event)
            await uow.commit()
