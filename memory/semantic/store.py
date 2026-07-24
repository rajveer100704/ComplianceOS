"""Semantic Memory Store (Clause embeddings & regulatory standards)."""

from memory.base import InMemoryStore
from memory.schemas import MemoryType


class SemanticMemoryStore(InMemoryStore):
    """Stores similar regulations, clauses, and standards embeddings."""

    memory_type = MemoryType.SEMANTIC
