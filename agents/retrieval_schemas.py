"""DTO schemas for Sprint 2.3 Evidence Retrieval Agent."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from document_processing.schemas import Requirement


class RetrievalTrace(BaseModel):
    """Detailed trace log for multi-stage retrieval execution and observability."""

    model_config = ConfigDict(from_attributes=True)

    dense_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    source: str = "hybrid"
    parent_id: Optional[str] = None
    dense_latency_ms: float = 0.0
    bm25_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    embedding_model: str = "all-MiniLM-L6-v2"
    reranker: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    filters: Dict[str, Any] = Field(default_factory=dict)


class RetrievalContext(BaseModel):
    """Context artifact containing retrieved chunks, parent docs, tables, figures, and trace data."""

    model_config = ConfigDict(from_attributes=True)

    query: str
    requirement_id: Optional[str] = None
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    parent_documents: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    figures: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    trace: Optional[RetrievalTrace] = None


class EvidenceBundle(BaseModel):
    """Rich evidence package pairing a requirement with its retrieved context and linked document elements."""

    model_config = ConfigDict(from_attributes=True)

    requirement: Requirement
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    linked_tables: List[Dict[str, Any]] = Field(default_factory=list)
    linked_figures: List[Dict[str, Any]] = Field(default_factory=list)
    linked_captions: List[str] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    context: Optional[RetrievalContext] = None
