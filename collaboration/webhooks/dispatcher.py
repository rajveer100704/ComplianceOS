"""Activity event stream dispatcher indexing events to Memory and Knowledge Graph."""

import logging
from typing import List, Dict, Optional
from collaboration.schemas import ActivityEvent
from memory.manager import MemoryManager
from memory.schemas import MemoryItem, MemoryType
from knowledge_graph.manager import KnowledgeGraphManager

logger = logging.getLogger("collaboration.webhooks.dispatcher")


class ActivityEventDispatcher:
    """Emits audit activity events to memory subsystem and Knowledge Graph."""

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        graph_manager: Optional[KnowledgeGraphManager] = None,
    ):
        self.memory_manager = memory_manager
        self.graph_manager = graph_manager
        self._events: Dict[str, List[ActivityEvent]] = (
            {}
        )  # session_id -> List[ActivityEvent]

    async def dispatch(self, event: ActivityEvent) -> ActivityEvent:
        if event.session_id not in self._events:
            self._events[event.session_id] = []
        self._events[event.session_id].append(event)

        logger.info(
            f"Dispatched ActivityEvent '{event.event_type}' by actor '{event.actor_id}' in session '{event.session_id}'"
        )

        # Emit to Reviewer Memory tier if memory_manager is configured
        if self.memory_manager:
            mem_item = MemoryItem(
                id=f"mem-act-{event.id}",
                organization_id=event.organization_id,
                memory_type=MemoryType.REVIEWER,
                content=f"Audit Event {event.event_type} by actor {event.actor_id} on {event.target_entity_id}",
                source_agent=f"Actor:{event.actor_id}",
                linked_entity_ids=[event.target_entity_id],
            )
            await self.memory_manager.store(mem_item)

        return event

    async def get_events(self, session_id: str) -> List[ActivityEvent]:
        return self._events.get(session_id, [])
