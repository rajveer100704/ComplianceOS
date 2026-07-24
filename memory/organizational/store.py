"""Organizational Memory Store (Tenant policies & guidelines)."""

from memory.base import InMemoryStore
from memory.schemas import MemoryType


class OrganizationalMemoryStore(InMemoryStore):
    """Stores tenant-specific compliance policies and organizational guidelines."""

    memory_type = MemoryType.ORGANIZATIONAL
