"""Canonical DTOs and models for Shared Memory Engine (Sprint 3)."""

import uuid
import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MemoryType(str, Enum):
    SEMANTIC = "semantic"  # Similar regulations & clause embeddings
    EPISODIC = "episodic"  # Execution trajectories & reasoning traces
    ORGANIZATIONAL = "organizational"  # Tenant policies & organization standards
    REVIEWER = "reviewer"  # Reviewer preferences & past override feedback
    WORKFLOW = "workflow"  # Execution graph state checkpoints


class MemoryItem(BaseModel):
    """Individual memory item entry with provenance, version identity, and Knowledge Graph link hooks."""

    model_config = ConfigDict(from_attributes=True)

    id: str  # Permanent identity (equivalent to logical_id)
    logical_id: Optional[str] = None  # Explicit permanent identity
    record_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )  # Unique storage row ID
    organization_id: str = "default"
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance_score: float = 1.0  # 0.0 (Trivial) to 1.0 (Critical)
    relevance_score: float = 1.0  # Computed dynamically during retrieval
    ttl_seconds: Optional[int] = None
    version: str = "v1.0.0"
    is_latest: bool = True
    checksum: Optional[str] = None
    source_agent: Optional[str] = None
    source_entity: Optional[str] = None
    linked_entity_ids: List[str] = Field(default_factory=list)
    embedding_id: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    graph_node_id: Optional[str] = None
    graph_edge_ids: List[str] = Field(default_factory=list)
    is_archived: bool = False
    is_pinned: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def populate_defaults(self) -> "MemoryItem":
        if not self.logical_id:
            self.logical_id = self.id
        if not self.checksum and self.content:
            self.checksum = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        return self


class MemoryQuery(BaseModel):
    """Query parameter container for memory retrieval."""

    model_config = ConfigDict(from_attributes=True)

    query_text: str
    organization_id: str = "default"
    memory_types: List[MemoryType] = Field(default_factory=list)
    top_k: int = 5
    min_importance: float = 0.0
    include_archived: bool = False
    filters: Dict[str, Any] = Field(default_factory=dict)


class MemoryContext(BaseModel):
    """Token-budgeted, unified memory context bundle handed to agents."""

    model_config = ConfigDict(from_attributes=True)

    query: str
    organization_id: str
    semantic_memories: List[MemoryItem] = Field(default_factory=list)
    episodic_memories: List[MemoryItem] = Field(default_factory=list)
    organizational_memories: List[MemoryItem] = Field(default_factory=list)
    reviewer_memories: List[MemoryItem] = Field(default_factory=list)
    workflow_memories: List[MemoryItem] = Field(default_factory=list)
    total_tokens: int = 0
    token_budget: int = 2000
    compressed_summary: Optional[str] = None
