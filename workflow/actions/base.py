"""BaseWorkflowAction interface for pluggable workflow action handlers."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from workflow.context import WorkflowContext
from workflow.retry import RetryPolicy


class BaseWorkflowAction(ABC):
    """Abstract interface implemented by all workflow action plugins."""

    @property
    @abstractmethod
    def action_key(self) -> str:
        """Unique identifier key for this workflow action plugin."""
        pass

    @property
    def retry_policy(self) -> RetryPolicy:
        """Configured retry strategy for this action (default: EXPONENTIAL)."""
        return RetryPolicy.EXPONENTIAL

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        """Executes the action logic and returns result dictionary."""
        pass

    async def rollback(self, context: WorkflowContext) -> bool:
        """Rolls back side-effects if workflow fails downstream (default no-op)."""
        return True

    async def simulate(self, context: WorkflowContext) -> Dict[str, Any]:
        """Simulates action execution in dry-run mode without mutating production state."""
        return {
            "status": "SIMULATED",
            "action_key": self.action_key,
            "dry_run": True,
            "message": f"Action '{self.action_key}' simulated cleanly.",
        }
