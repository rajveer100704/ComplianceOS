"""Async event bus for real-time agent thought, tool execution, and state streaming."""

import asyncio
import logging
from typing import Dict, Any, List, AsyncGenerator
from agent_runtime.interfaces import BaseEventBus

logger = logging.getLogger("agent_runtime.events")


class AgentEventBus(BaseEventBus):
    """In-memory async event bus managing channel subscriptions and event broadcasting."""

    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    async def publish(self, channel: str, event: Dict[str, Any]) -> None:
        """Publishes event payload to all active channel queues."""
        if channel not in self._subscribers:
            return

        queues = self._subscribers[channel]
        for q in queues:
            await q.put(event)
        logger.debug(
            f"Published event to {len(queues)} subscriber(s) on channel '{channel}'"
        )

    async def subscribe(self, channel: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribes to an event channel, yielding events as they arrive."""
        queue: asyncio.Queue = asyncio.Queue()
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(queue)

        try:
            while True:
                event = await queue.get()
                yield event
                queue.task_done()
        finally:
            if channel in self._subscribers and queue in self._subscribers[channel]:
                self._subscribers[channel].remove(queue)
                if not self._subscribers[channel]:
                    del self._subscribers[channel]


# Singleton instance
agent_event_bus = AgentEventBus()
