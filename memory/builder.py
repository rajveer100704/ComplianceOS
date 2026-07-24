"""MemoryContextBuilder creating unified, token-budgeted MemoryContext objects for agents."""

import logging
from typing import List
from memory.schemas import MemoryItem, MemoryContext, MemoryType
from memory.ranking import MemoryRanker
from memory.compression import MemoryCompressor
from memory.expiration import MemoryExpirationManager

logger = logging.getLogger("memory.builder")


class MemoryContextBuilder:
    """Builds token-budgeted, unified MemoryContext objects from raw memory items."""

    def __init__(self):
        self.ranker = MemoryRanker()
        self.compressor = MemoryCompressor()
        self.expiration_manager = MemoryExpirationManager()

    def build(
        self,
        raw_items: List[MemoryItem],
        query_text: str,
        organization_id: str,
        token_budget: int = 2000,
    ) -> MemoryContext:
        # 1. Filter expired memory items
        valid_items = self.expiration_manager.filter_expired(raw_items)

        # 2. Rank by relevance and importance
        ranked_items = self.ranker.rank(valid_items, query_text)

        # 3. Categorize by tier
        semantic = [i for i in ranked_items if i.memory_type == MemoryType.SEMANTIC]
        episodic = [i for i in ranked_items if i.memory_type == MemoryType.EPISODIC]
        organizational = [
            i for i in ranked_items if i.memory_type == MemoryType.ORGANIZATIONAL
        ]
        reviewer = [i for i in ranked_items if i.memory_type == MemoryType.REVIEWER]
        workflow = [i for i in ranked_items if i.memory_type == MemoryType.WORKFLOW]

        # 4. Generate compressed summary
        summary = self.compressor.compress(ranked_items[:5], max_summary_tokens=500)

        # Estimated token count
        total_tokens = sum(len(i.content.split()) for i in ranked_items)

        logger.debug(
            f"Built MemoryContext for org '{organization_id}': total_tokens={total_tokens}, semantic={len(semantic)}, episodic={len(episodic)}"
        )

        return MemoryContext(
            query=query_text,
            organization_id=organization_id,
            semantic_memories=semantic,
            episodic_memories=episodic,
            organizational_memories=organizational,
            reviewer_memories=reviewer,
            workflow_memories=workflow,
            total_tokens=total_tokens,
            token_budget=token_budget,
            compressed_summary=summary,
        )
