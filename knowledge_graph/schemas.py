"""Canonical DTOs and models for Regulatory Knowledge Graph Engine (Sprint 4)."""

import uuid
import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field, model_validator


class NodeType(str, Enum):
    REGULATION = "REGULATION"  # Regulatory standards (FAA Part 450, ASME BPVC)
    REQUIREMENT = "REQUIREMENT"  # Extracted clause requirements
    CLAIM = "CLAIM"  # Engineering claims undergoing compliance check
    EVIDENCE = "EVIDENCE"  # Pinned text snippets, table cells, telemetry
    DECISION = "DECISION"  # Verification result & grounding scores
    MEMORY = "MEMORY"  # Sprint 3 MemoryItem entries


class EdgeType(str, Enum):
    CONTAINS = "CONTAINS"  # REGULATION -> REQUIREMENT
    REQUIRES = "REQUIRES"  # CLAIM -> REQUIREMENT
    SUPPORTS = "SUPPORTS"  # EVIDENCE -> CLAIM
    CONTRADICTS = "CONTRADICTS"  # EVIDENCE -> CLAIM
    VERIFIES = "VERIFIES"  # DECISION -> CLAIM
    CITES = "CITES"  # DECISION -> EVIDENCE
    GENERATED_BY = "GENERATED_BY"  # DECISION -> MEMORY
    SUPERSEDES = "SUPERSEDES"  # REGULATION (v2) -> REGULATION (v1)


class GraphNode(BaseModel):
    """Canonical graph vertex model."""

    model_config = ConfigDict(from_attributes=True)

    id: str  # Unique Node ID (e.g. node-req-450.115)
    logical_id: Optional[str] = None
    organization_id: str = "default"
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    checksum: Optional[str] = None
    source_agent: Optional[str] = None
    version: str = "v1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def populate_defaults(self) -> "GraphNode":
        if not self.logical_id:
            self.logical_id = self.id
        if not self.checksum:
            content_str = f"{self.node_type.value}:{self.label}:{str(self.properties)}"
            self.checksum = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
        return self


class GraphEdge(BaseModel):
    """Canonical directed graph edge model."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: f"edge-{uuid.uuid4().hex[:8]}")
    organization_id: str = "default"
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    weight: float = 1.0  # Relationship strength / confidence score (0.0 to 1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SubGraph(BaseModel):
    """Sub-graph container holding node and edge collections."""

    model_config = ConfigDict(from_attributes=True)

    organization_id: str = "default"
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


class GraphPath(BaseModel):
    """Path trace connecting a source node to a target node through multi-hop traversal."""

    model_config = ConfigDict(from_attributes=True)

    source_node_id: str
    target_node_id: str
    hops: int = 0
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
