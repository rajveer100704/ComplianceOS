"""Canonical models and schemas for Verification Engine (Sprint 2.4)."""

import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field
from document_processing.schemas import Requirement
from agents.retrieval_schemas import EvidenceBundle


class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"


class PromptVersion(BaseModel):
    """Immutable prompt template version tracker."""

    id: str
    template: str
    checksum: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, version_id: str, template: str) -> "PromptVersion":
        checksum = hashlib.sha256(template.encode("utf-8")).hexdigest()
        return cls(id=version_id, template=template, checksum=checksum)


class VerificationTrace(BaseModel):
    """Detailed trace log for verification reasoning, citations, tokens, and prompt/policy versions."""

    model_config = ConfigDict(from_attributes=True)

    reasoning_steps: List[str] = Field(default_factory=list)
    retrieval_ids: List[str] = Field(default_factory=list)
    citations_used: List[str] = Field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = "gemini-2.0-flash"
    prompt_version: str = "v1.0.0"
    policy_version: Optional[str] = None


class VerificationContext(BaseModel):
    """Deterministic context bundle supplied to the verifier pipeline."""

    model_config = ConfigDict(from_attributes=True)

    requirement: Requirement
    evidence_bundle: EvidenceBundle
    policy_rules: List[Dict[str, Any]] = Field(default_factory=list)
    organization_id: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    """Rich verification output pairing decision status with grounding score, citations, and policy decisions."""

    model_config = ConfigDict(from_attributes=True)

    claim_id: str
    requirement_id: str
    status: VerificationStatus
    confidence: float = 1.0
    reasoning: str
    citations: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    hallucination_risk: float = 0.0
    grounding_score: float = 1.0
    policy_decision: Dict[str, Any] = Field(default_factory=dict)
    trace: Optional[VerificationTrace] = None
