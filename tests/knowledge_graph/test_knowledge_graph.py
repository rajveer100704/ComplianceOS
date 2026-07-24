"""Unit & integration tests for Regulatory Knowledge Graph Engine (Sprint 4)."""

import pytest
from knowledge_graph import (
    KnowledgeGraphManager,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
)
from memory.schemas import MemoryItem, MemoryType


@pytest.mark.asyncio
async def test_knowledge_graph_manager_node_and_edge_indexing():
    mgr = KnowledgeGraphManager()

    # Index requirement
    req_node = await mgr.index_requirement(
        req_id="450.115-a",
        text="Public risk must not exceed 1e-4 expected casualties.",
        section="Flight Safety Analysis",
        organization_id="org-acme",
    )
    assert req_node.node_type == NodeType.REQUIREMENT
    assert req_node.checksum is not None

    # Index claim
    claim_node = await mgr.index_claim(
        claim_id="CLM-001",
        text="Trajectory debris analysis verifies casualty expectancy < 1e-4.",
        req_id="450.115-a",
        organization_id="org-acme",
    )
    assert claim_node.node_type == NodeType.CLAIM

    # Index evidence
    evi_node = await mgr.index_evidence(
        evidence_id="EVI-001",
        snippet="Debris dispersal simulation yields 3.2e-5 expected casualties.",
        claim_id="CLM-001",
        is_supporting=True,
        organization_id="org-acme",
    )
    assert evi_node.node_type == NodeType.EVIDENCE

    # Multi-hop path traversal from Evidence -> Claim -> Requirement
    paths = await mgr.find_paths(
        source_node_id=evi_node.id,
        target_node_types=[NodeType.REQUIREMENT],
        max_depth=3,
        organization_id="org-acme",
    )
    assert len(paths) >= 1
    assert paths[0].target_node_id == req_node.id


@pytest.mark.asyncio
async def test_memory_to_graph_linkage():
    mgr = KnowledgeGraphManager()

    # Create requirement & claim in graph first
    await mgr.index_claim(
        claim_id="CLM-002",
        text="Thermal protection system complies with ASME BPVC.",
        organization_id="org-acme",
    )

    # Sprint 3 MemoryItem referencing linked claim
    memory_item = MemoryItem(
        id="mem-exp-101",
        organization_id="org-acme",
        memory_type=MemoryType.EPISODIC,
        content="Prior verification trace for thermal protection system.",
        source_agent="VerificationAgent",
        linked_entity_ids=["CLM-002"],
    )

    mem_node = await mgr.index_memory(memory_item)
    assert mem_node.node_type == NodeType.MEMORY
    assert mem_node.version == "v1.0.0"

    # Verify neighborhood extraction includes memory node
    subgraph = await mgr.get_neighborhood(
        mem_node.id, depth=1, organization_id="org-acme"
    )
    assert len(subgraph.nodes) >= 2


@pytest.mark.asyncio
async def test_knowledge_graph_impact_analysis():
    mgr = KnowledgeGraphManager()

    # Construct standard regulation -> requirement -> claim graph
    reg_node = GraphNode(
        id="node-reg-faa-450",
        organization_id="org-acme",
        node_type=NodeType.REGULATION,
        label="FAA Part 450 Safety Standard",
    )
    await mgr.add_node(reg_node)

    req_node = await mgr.index_requirement(
        "450.115-b", "Public risk analysis required", "Safety", "org-acme"
    )

    # Connect regulation -> requirement
    edge = GraphEdge(
        organization_id="org-acme",
        source_node_id=reg_node.id,
        target_node_id=req_node.id,
        edge_type=EdgeType.CONTAINS,
    )
    await mgr.add_edge(edge)

    # Impact query
    impact = await mgr.query_impact("node-reg-faa-450", organization_id="org-acme")
    assert impact["total_impacted_count"] == 1
    assert req_node.id in impact["impacted_requirements"]
