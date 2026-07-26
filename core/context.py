"""Unified ExecutionContext model carrying request, tenant, budget, and cancellation state (Sprint 3)."""

import uuid
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field


class ExecutionContext(BaseModel):
    """Unified context passed across subsystem boundaries."""

    model_config = ConfigDict(from_attributes=True)

    trace_id: str = Field(default_factory=lambda: f"trace-{uuid.uuid4().hex[:12]}")
    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}")
    organization_id: str = "default"
    user_id: str = "system"
    roles: list[str] = Field(default_factory=lambda: ["user"])
    token_budget: int = 4000
    latency_budget_ms: float = 5000.0
    cancellation_requested: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def is_cancelled(self) -> bool:
        return self.cancellation_requested
