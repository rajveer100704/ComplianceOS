"""Async CheckpointStore persisting AgentRuntimeState across execution threads."""

import uuid
import logging
from typing import Optional, Dict

from agent_runtime.interfaces import BaseCheckpointStore, BaseAgentState

logger = logging.getLogger("agent_runtime.checkpoint")


class InMemoryCheckpointStore(BaseCheckpointStore):
    """In-memory checkpoint store for local execution, unit testing, and fast recovery."""

    def __init__(self):
        self._checkpoints: Dict[str, BaseAgentState] = {}

    async def save_checkpoint(self, thread_id: str, state: BaseAgentState) -> str:
        checkpoint_id = str(uuid.uuid4())
        # Store state copy
        self._checkpoints[thread_id] = state.model_copy(deep=True)
        logger.debug(
            f"Saved in-memory checkpoint {checkpoint_id} for thread {thread_id}"
        )
        return checkpoint_id

    async def load_checkpoint(self, thread_id: str) -> Optional[BaseAgentState]:
        state = self._checkpoints.get(thread_id)
        if state:
            return state.model_copy(deep=True)
        return None
