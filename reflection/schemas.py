"""Canonical models and schemas for Reflection & Critique Subsystem (Sprint 2.7)."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReflectionDecision(str, Enum):
    APPROVED = "APPROVED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    REQUIRES_RERUN = "REQUIRES_RERUN"


class ReflectionTrace(BaseModel):
    """Trace log for reflection execution, checks performed, latency, and tokens."""

    model_config = ConfigDict(from_attributes=True)

    prompt_version: str = "v1.0.0"
    checks_performed: List[str] = Field(default_factory=list)
    citations_checked: int = 0
    sections_checked: int = 0
    confidence: float = 1.0
    latency_ms: float = 0.0
    tokens_used: int = 0


class ReflectionContext(BaseModel):
    """Deterministic context bundle supplied to the reflection critique engine."""

    model_config = ConfigDict(from_attributes=True)

    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    verification_results: List[Dict[str, Any]] = Field(default_factory=list)
    risk_results: Optional[Dict[str, Any]] = None
    structured_report: Optional[Dict[str, Any]] = None
    policy_results: List[Dict[str, Any]] = Field(default_factory=list)
    organization_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReflectionResult(BaseModel):
    """Structured QA critique output and decision gate."""

    model_config = ConfigDict(from_attributes=True)

    overall_score: float = 1.0
    confidence: float = 1.0
    hallucination_risk: float = 0.0
    missing_citations: List[str] = Field(default_factory=list)
    consistency_errors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    decision: ReflectionDecision = ReflectionDecision.APPROVED
    requires_rerun: bool = False
    rerun_target_agent: Optional[str] = None
    trace: Optional[ReflectionTrace] = None
