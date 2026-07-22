import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.outbox import OutboxEventModel
from database.services.unit_of_work import UnitOfWork

logger = logging.getLogger("complianceos.database.events")


class EventPublisher:
    """Enqueues events in the outbox table for reliable background execution."""

    @staticmethod
    async def publish_event(
        event_type: str,
        payload: Dict[str, Any],
        session: Optional[AsyncSession] = None,
    ) -> None:
        if session is not None:
            event = OutboxEventModel(event_type=event_type, payload=payload)
            session.add(event)
            return

        try:
            async with UnitOfWork() as uow:
                event = OutboxEventModel(event_type=event_type, payload=payload)
                uow.session.add(event)
                await uow.commit()
        except Exception as e:
            logger.warning(f"Could not publish outbox event '{event_type}': {e}")
