"""Unified PlatformEvent domain model for cross-cutting AI Governance, Audit, and Subsystem Observation."""

import uuid
from enum import Enum
from typing import Dict, Any
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field


class EventCategory(str, Enum):
    COLLABORATION = "COLLABORATION"
    MEMORY = "MEMORY"
    KNOWLEDGE_GRAPH = "KNOWLEDGE_GRAPH"
    POLICY = "POLICY"
    AGENT_RUNTIME = "AGENT_RUNTIME"
    SYSTEM = "SYSTEM"


class PlatformEvent(BaseModel):
    """Unified cross-cutting domain event contract emitted by all subsystems."""

    model_config = ConfigDict(from_attributes=True)

    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    event_type: (
        str  # e.g. LOCK_ACQUIRED, MEMORY_STORED, GRAPH_NODE_ADDED, POLICY_EVALUATED
    )
    category: EventCategory
    organization_id: str = "default"
    actor_id: str
    target_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
