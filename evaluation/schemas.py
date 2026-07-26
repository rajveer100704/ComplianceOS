"""Canonical DTOs and models for Benchmark Suite & Evaluation Engine (Sprint 7)."""

import uuid
from typing import Dict, Any, List
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field


class BenchmarkTestCase(BaseModel):
    """Standardized input test case for regulatory benchmark evaluation."""

    model_config = ConfigDict(from_attributes=True)

    case_id: str = Field(default_factory=lambda: f"case-{uuid.uuid4().hex[:8]}")
    dataset_id: str = "faa-part-450"
    organization_id: str = "default"
    query_text: str
    expected_document_ids: List[str] = Field(default_factory=list)
    expected_claims: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationRun(BaseModel):
    """Aggregated result of executing a benchmark test suite run."""

    model_config = ConfigDict(from_attributes=True)

    run_id: str = Field(default_factory=lambda: f"run-{uuid.uuid4().hex[:8]}")
    dataset_id: str = "faa-part-450"
    organization_id: str = "default"
    total_cases_evaluated: int = 0
    recall_at_5: float = 0.0
    mrr: float = 0.0
    mean_grounding_score: float = 0.0
    mean_latency_ms: float = 0.0
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RegressionReport(BaseModel):
    """Quantitative comparison between baseline and current evaluation runs."""

    model_config = ConfigDict(from_attributes=True)

    report_id: str = Field(default_factory=lambda: f"regr-{uuid.uuid4().hex[:8]}")
    organization_id: str = "default"
    baseline_run_id: str
    current_run_id: str
    is_regression: bool = False
    delta_recall_at_5: float = 0.0
    delta_mrr: float = 0.0
    delta_grounding_score: float = 0.0
    delta_latency_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
