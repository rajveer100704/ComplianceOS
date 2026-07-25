"""Lightweight asynchronous EventBus for cross-cutting PlatformEvent publish/subscribe."""

import logging
from typing import Callable, Awaitable, Dict, List, Optional
from events.schemas import PlatformEvent, EventCategory

logger = logging.getLogger("events.bus")

SubscriberCallback = Callable[[PlatformEvent], Awaitable[None]]


class EventBus:
    """Asynchronous event bus routing PlatformEvent instances to registered category subscribers."""

    def __init__(self):
        self._subscribers: Dict[Optional[EventCategory], List[SubscriberCallback]] = {}

    def subscribe(
        self,
        callback: SubscriberCallback,
        category: Optional[EventCategory] = None,
    ) -> None:
        """Registers a subscriber callback for a specific event category or all events (category=None)."""
        if category not in self._subscribers:
            self._subscribers[category] = []
        self._subscribers[category].append(callback)
        logger.debug(f"Subscribed callback to EventCategory '{category or 'ALL'}'")

    async def publish(self, event: PlatformEvent) -> int:
        """Publishes a PlatformEvent to matching category subscribers and wildcard subscribers."""
        delivered_count = 0

        # Category-specific subscribers
        category_subs = self._subscribers.get(event.category, [])
        # Wildcard subscribers (category=None)
        wildcard_subs = self._subscribers.get(None, [])

        all_subs = category_subs + wildcard_subs
        for cb in all_subs:
            try:
                await cb(event)
                delivered_count += 1
            except Exception as e:
                logger.error(
                    f"Error in subscriber callback for event '{event.event_id}': {e}",
                    exc_info=True,
                )

        logger.info(
            f"Published PlatformEvent '{event.event_type}' ({event.event_id}) to {delivered_count} subscriber(s)"
        )
        return delivered_count

    def clear(self) -> None:
        """Clears all registered subscribers."""
        self._subscribers.clear()
