"""ActionRegistry managing pluggable workflow action plugins."""

from typing import Dict, List, Optional
from workflow.actions.base import BaseWorkflowAction


class ActionRegistry:
    """Registry maintaining active workflow action plugin instances."""

    def __init__(self):
        self._actions: Dict[str, BaseWorkflowAction] = {}

    def register(self, action: BaseWorkflowAction):
        """Registers a workflow action plugin instance."""
        self._actions[action.action_key] = action

    def get(self, action_key: str) -> Optional[BaseWorkflowAction]:
        """Retrieves registered action instance by key."""
        return self._actions.get(action_key)

    def list_actions(self) -> List[str]:
        """Lists all registered action keys."""
        return list(self._actions.keys())

    def clear(self):
        """Clears all registered action plugins."""
        self._actions.clear()


# Global ActionRegistry singleton
action_registry = ActionRegistry()
