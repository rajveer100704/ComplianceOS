"""Memory importance and temporal decay scorer."""

import logging
from datetime import datetime, UTC
from memory.schemas import MemoryItem

logger = logging.getLogger("memory.importance")


class MemoryImportanceScorer:
    """Computes importance scores and applies temporal decay to memory items."""

    def compute_decay(self, item: MemoryItem, half_life_days: float = 30.0) -> float:
        now = datetime.now(UTC)
        age_days = (now - item.created_at).total_seconds() / 86400.0
        decay_factor = 0.5 ** (age_days / max(1.0, half_life_days))
        effective_importance = round(item.importance_score * decay_factor, 2)
        logger.debug(
            f"Memory '{item.id}' age={age_days:.1f}d, decayed importance={effective_importance}"
        )
        return effective_importance
