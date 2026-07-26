"""Canonical Evidence and Grounding domain models (Sprint 4)."""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    """Citation linking evidence to a specific standard or regulatory section."""

    model_config = ConfigDict(from_attributes=True)

    standard_id: str
    section_number: Optional[str] = None
    title: str
    text_snippet: str
    url: Optional[str] = None


class Provenance(BaseModel):
    """Metadata tracking origin and chain-of-custody for evidence."""

    model_config = ConfigDict(from_attributes=True)

    source_system: str = "ComplianceOS"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retrieval_method: str = "hybrid_vector_bm25"
    confidence_score: float = 1.0


class Evidence(BaseModel):
    """Unified Evidence DTO consumed across Retrieval, Graph, Governance, and MCP."""

    model_config = ConfigDict(from_attributes=True)

    evidence_id: str = Field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:8]}")
    claim_id: Optional[str] = None
    content: str
    citations: List[Citation] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """Aggregated bundle of evidence for claim verification."""

    model_config = ConfigDict(from_attributes=True)

    bundle_id: str = Field(default_factory=lambda: f"bndl-{uuid.uuid4().hex[:8]}")
    claim_text: str
    evidences: List[Evidence] = Field(default_factory=list)
    overall_grounding_score: float = 0.0
    status: str = "SUPPORTED"
