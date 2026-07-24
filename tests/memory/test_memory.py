"""Unit & integration tests for Shared Memory Engine (Sprint 3)."""

import pytest
from memory import (
    MemoryManager,
    MemoryItem,
    MemoryType,
    MemoryQuery,
    MemoryContext,
    MemoryRanker,
    MemoryImportanceScorer,
    MemoryCompressor,
    MemoryExpirationManager,
)


@pytest.mark.asyncio
async def test_memory_manager_crud_and_tier_isolation():
    manager = MemoryManager()

    item_sem = MemoryItem(
        id="mem-sem-001",
        organization_id="org-acme",
        memory_type=MemoryType.SEMANTIC,
        content="FAA Part 450 launch safety criteria regulation.",
        importance_score=0.9,
        source_agent="RequirementAnalysisAgent",
        source_entity="REQ-001",
        linked_entity_ids=["CLM-001"],
        graph_node_id="node-101",
        graph_edge_ids=["edge-501"],
    )
    item_org = MemoryItem(
        id="mem-org-001",
        organization_id="org-acme",
        memory_type=MemoryType.ORGANIZATIONAL,
        content="ACME internal dual-approval safety policy for mandatory clauses.",
        importance_score=0.95,
        source_agent="PolicyEngine",
    )

    # Automatic checksum assertion & logical_id default
    assert item_sem.checksum is not None
    assert len(item_sem.checksum) == 64
    assert item_sem.logical_id == "mem-sem-001"
    assert item_sem.record_id is not None

    await manager.store(item_sem)
    await manager.store(item_org)

    # Search for semantic memories only
    q_sem = MemoryQuery(
        query_text="FAA",
        organization_id="org-acme",
        memory_types=[MemoryType.SEMANTIC],
    )
    results_sem = await manager.search(q_sem)
    assert len(results_sem) == 1
    assert results_sem[0].id == "mem-sem-001"
    assert results_sem[0].source_agent == "RequirementAnalysisAgent"
    assert results_sem[0].graph_node_id == "node-101"

    # Unified context building
    context: MemoryContext = await manager.build_context(
        query_text="safety", organization_id="org-acme", token_budget=2000
    )
    assert len(context.semantic_memories) == 1
    assert len(context.organizational_memories) == 1
    assert context.total_tokens > 0


@pytest.mark.asyncio
async def test_memory_append_only_version_history():
    manager = MemoryManager()

    item = MemoryItem(
        id="mem-ver-001",
        organization_id="org-acme",
        memory_type=MemoryType.REVIEWER,
        content="Initial reviewer guideline.",
        importance_score=0.9,
    )

    # v1.0.0 store
    await manager.store(item)
    assert item.version == "v1.0.0"

    # v1.0.1 pin
    pinned = await manager.pin_memory("mem-ver-001", MemoryType.REVIEWER)
    assert pinned is not None
    assert pinned.version == "v1.0.1"

    # v1.0.2 archive
    archived = await manager.archive_memory("mem-ver-001", MemoryType.REVIEWER)
    assert archived is not None
    assert archived.version == "v1.0.2"

    # Verify history maintains all 3 versions simultaneously!
    history = await manager.history("mem-ver-001", MemoryType.REVIEWER)
    assert len(history) == 3
    assert history[0].version == "v1.0.0"
    assert history[0].is_latest is False
    assert history[1].version == "v1.0.1"
    assert history[1].is_latest is False
    assert history[2].version == "v1.0.2"
    assert history[2].is_latest is True

    # Unique storage row record_ids
    record_ids = {h.record_id for h in history}
    assert len(record_ids) == 3

    # Latest version query
    latest_item = await manager.latest("mem-ver-001", MemoryType.REVIEWER)
    assert latest_item is not None
    assert latest_item.version == "v1.0.2"


@pytest.mark.asyncio
async def test_memory_intelligence_pipeline():
    ranker = MemoryRanker()
    scorer = MemoryImportanceScorer()
    compressor = MemoryCompressor()
    expiration = MemoryExpirationManager()

    item = MemoryItem(
        id="mem-001",
        organization_id="org-1",
        memory_type=MemoryType.EPISODIC,
        content="Previous execution trajectory for FAA 450.115.",
        importance_score=0.8,
        ttl_seconds=3600,
    )

    # Decay check
    decayed = scorer.compute_decay(item, half_life_days=30.0)
    assert decayed <= 0.8

    # Expiration check
    valid = expiration.filter_expired([item])
    assert len(valid) == 1

    # Ranking check
    ranked = ranker.rank([item], query_text="FAA")
    assert ranked[0].relevance_score > 0.5

    # Compression check
    summary = compressor.compress([item])
    assert "[EPISODIC]" in summary
