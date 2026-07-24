"""Reviewer Memory Store (Reviewer preferences & override feedback)."""

from memory.base import InMemoryStore
from memory.schemas import MemoryType


class ReviewerMemoryStore(InMemoryStore):
    """Stores reviewer preferences, past overrides, and feedback comments."""

    memory_type = MemoryType.REVIEWER
