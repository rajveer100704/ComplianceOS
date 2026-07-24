"""Workflow Memory Store (Execution graph state checkpoints)."""

from memory.base import InMemoryStore
from memory.schemas import MemoryType


class WorkflowMemoryStore(InMemoryStore):
    """Stores execution graph state checkpoints for state restoration."""

    memory_type = MemoryType.WORKFLOW
