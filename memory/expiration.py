"""TTL and memory expiration manager."""

import logging
from datetime import datetime, UTC
from typing import List
from memory.schemas import MemoryItem

logger = logging.getLogger("memory.expiration")


class MemoryExpirationManager:
    """Filters out expired memory items based on TTL seconds."""

    def filter_expired(self, items: List[MemoryItem]) -> List[MemoryItem]:
        now = datetime.now(UTC)
        valid_items: List[MemoryItem] = []

        for item in items:
            if item.ttl_seconds is not None:
                age_seconds = (now - item.created_at).total_seconds()
                if age_seconds > item.ttl_seconds:
                    logger.debug(
                        f"Memory item '{item.id}' expired (age {age_seconds}s > ttl {item.ttl_seconds}s)"
                    )
                    continue
            valid_items.append(item)

        return valid_items
