"""Episodic Memory Store (Execution trajectories & reasoning steps)."""

from memory.base import InMemoryStore
from memory.schemas import MemoryType


class EpisodicMemoryStore(InMemoryStore):
    """Stores execution trajectories and agent reasoning logs."""

    memory_type = MemoryType.EPISODIC
