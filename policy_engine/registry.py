"""PolicyRegistry mapping DomainEventCatalog types to registered policy evaluators."""

from typing import Dict, List, Callable, Any
from events.catalog import DomainEventCatalog
from policy_engine.context import PolicyContext
from policy_engine.decision import PolicyDecision


class PolicyRegistry:
    """Event-driven registry mapping domain event types to evaluator handlers."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable[[PolicyContext], PolicyDecision]]] = {}

    def register(
        self, event_type: DomainEventCatalog, handler: Callable[[PolicyContext], PolicyDecision]
    ):
        """Registers an evaluator handler function for a domain event type."""
        key = event_type.value if hasattr(event_type, "value") else str(event_type)
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(handler)

    def get_handlers(
        self, event_type: DomainEventCatalog
    ) -> List[Callable[[PolicyContext], PolicyDecision]]:
        """Retrieves all evaluator handlers for a domain event type."""
        key = event_type.value if hasattr(event_type, "value") else str(event_type)
        return self._handlers.get(key, [])

    def clear(self):
        """Clears all registered handlers."""
        self._handlers.clear()


# Global policy registry singleton
policy_registry = PolicyRegistry()
