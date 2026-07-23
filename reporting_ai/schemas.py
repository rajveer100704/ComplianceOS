"""Canonical models and schemas for AI Reporting Engine (Sprint 2.6)."""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field


class ReportFormat(str, Enum):
    EXECUTIVE = "EXECUTIVE"
    TECHNICAL = "TECHNICAL"
    AUDIT = "AUDIT"
    REGULATORY = "REGULATORY"
    INTERNAL_REVIEW = "INTERNAL_REVIEW"


class ReportSection(BaseModel):
    """Structured report section entry."""

    id: str
    title: str
    content: str
    order: int
    citations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReportTrace(BaseModel):
    """Trace log for report generation timing, token usage, prompt version, and validation checks."""

    model_config = ConfigDict(from_attributes=True)

    prompt_version: str = "v1.0.0"
    generation_time_ms: float = 0.0
    tokens_used: int = 0
    sections_generated: int = 0
    validation_errors: List[str] = Field(default_factory=list)
    confidence: float = 1.0


class ReportContext(BaseModel):
    """Deterministic context bundle supplied to the report generation pipeline."""

    model_config = ConfigDict(from_attributes=True)

    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    verification_results: List[Dict[str, Any]] = Field(default_factory=list)
    risk_results: Optional[Dict[str, Any]] = None
    policy_results: List[Dict[str, Any]] = Field(default_factory=list)
    organization_id: str = "default"
    format: ReportFormat = ReportFormat.AUDIT
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StructuredReport(BaseModel):
    """Audit-ready structured compliance report artifact."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    summary: str
    sections: List[ReportSection] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    format: ReportFormat = ReportFormat.AUDIT
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    trace: Optional[ReportTrace] = None
