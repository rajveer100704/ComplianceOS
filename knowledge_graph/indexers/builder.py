"""GraphBuilder transforming domain entities into Knowledge Graph vertices and directed edges."""

import logging
from typing import Optional
from knowledge_graph.schemas import GraphNode, GraphEdge, NodeType, EdgeType
from knowledge_graph.store.base import BaseGraphStore
from knowledge_graph.indexers.resolution import EntityResolver
from memory.schemas import MemoryItem

logger = logging.getLogger("knowledge_graph.indexers.builder")


class GraphBuilder:
    """Transforms domain entities (Requirement, Claim, Evidence, Decision, Memory) into graph structures."""

    def __init__(self, store: BaseGraphStore):
        self.store = store
        self.resolver = EntityResolver(store)

    async def index_requirement(
        self, req_id: str, text: str, section: str, organization_id: str = "default"
    ) -> GraphNode:
        node = GraphNode(
            id=f"node-req-{req_id}",
            logical_id=req_id,
            organization_id=organization_id,
            node_type=NodeType.REQUIREMENT,
            label=f"Requirement {req_id} ({section})",
            properties={"text": text, "section": section},
            source_agent="RequirementAnalysisAgent",
        )
        return await self.resolver.resolve_or_create(node)

    async def index_claim(
        self,
        claim_id: str,
        text: str,
        req_id: Optional[str] = None,
        organization_id: str = "default",
    ) -> GraphNode:
        node = GraphNode(
            id=f"node-claim-{claim_id}",
            logical_id=claim_id,
            organization_id=organization_id,
            node_type=NodeType.CLAIM,
            label=f"Claim {claim_id}",
            properties={"text": text},
        )
        resolved_claim = await self.resolver.resolve_or_create(node)

        if req_id:
            req_node_id = f"node-req-{req_id}"
            edge = GraphEdge(
                organization_id=organization_id,
                source_node_id=resolved_claim.id,
                target_node_id=req_node_id,
                edge_type=EdgeType.REQUIRES,
            )
            await self.store.add_edge(edge)

        return resolved_claim

    async def index_evidence(
        self,
        evidence_id: str,
        snippet: str,
        claim_id: str,
        is_supporting: bool = True,
        organization_id: str = "default",
    ) -> GraphNode:
        node = GraphNode(
            id=f"node-evi-{evidence_id}",
            logical_id=evidence_id,
            organization_id=organization_id,
            node_type=NodeType.EVIDENCE,
            label=f"Evidence {evidence_id}",
            properties={"snippet": snippet},
            source_agent="EvidenceRetrievalAgent",
        )
        resolved_evi = await self.resolver.resolve_or_create(node)

        claim_node_id = f"node-claim-{claim_id}"
        edge_type = EdgeType.SUPPORTS if is_supporting else EdgeType.CONTRADICTS
        edge = GraphEdge(
            organization_id=organization_id,
            source_node_id=resolved_evi.id,
            target_node_id=claim_node_id,
            edge_type=edge_type,
        )
        await self.store.add_edge(edge)

        return resolved_evi

    async def index_memory_item(self, memory_item: MemoryItem) -> GraphNode:
        """Transforms a Sprint 3 MemoryItem into a Knowledge Graph MEMORY node."""
        node = GraphNode(
            id=f"node-mem-{memory_item.id}",
            logical_id=memory_item.logical_id or memory_item.id,
            organization_id=memory_item.organization_id,
            node_type=NodeType.MEMORY,
            label=f"Memory {memory_item.memory_type.value.upper()} ({memory_item.id})",
            properties={
                "content": memory_item.content,
                "memory_type": memory_item.memory_type.value,
                "importance_score": memory_item.importance_score,
            },
            source_agent=memory_item.source_agent or "MemorySubsystem",
            version=memory_item.version,
        )
        resolved_mem = await self.resolver.resolve_or_create(node)

        # Connect memory to linked entity nodes
        for target_entity_id in memory_item.linked_entity_ids:
            target_node_id = f"node-claim-{target_entity_id}"
            edge = GraphEdge(
                organization_id=memory_item.organization_id,
                source_node_id=resolved_mem.id,
                target_node_id=target_node_id,
                edge_type=EdgeType.GENERATED_BY,
            )
            await self.store.add_edge(edge)

        return resolved_mem
