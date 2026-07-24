"""Relevance and importance re-ranker for memory items."""

import logging
from typing import List
from memory.schemas import MemoryItem

logger = logging.getLogger("memory.ranking")


class MemoryRanker:
    """Ranks memory items by combining relevance score, importance score, and freshness."""

    def rank(self, items: List[MemoryItem], query_text: str) -> List[MemoryItem]:
        for item in items:
            # Simple keyword match relevance score booster
            kw_match = (
                0.2
                if query_text and query_text.lower() in item.content.lower()
                else 0.0
            )
            item.relevance_score = round(
                min(1.0, item.importance_score * 0.7 + kw_match + 0.1), 2
            )

        ranked = sorted(
            items, key=lambda x: (x.relevance_score, x.importance_score), reverse=True
        )
        logger.debug(f"Ranked {len(ranked)} memory item(s)")
        return ranked
