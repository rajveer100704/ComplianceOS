import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DomainEventType(str, Enum):
    """Typed domain event catalog preventing event string drift across ComplianceOS."""

    CLAIM_CREATED = "claim.created"
    CLAIM_UPDATED = "claim.updated"
    CLAIM_VERDICT_RECORDED = "claim.verdict_recorded"
    REPORT_COMPILED = "report.compiled"
    REPORT_PUBLISHED = "report.published"
    SNAPSHOT_CREATED = "snapshot.created"
    MEMBER_INVITED = "member.invited"
    ORGANIZATION_CREATED = "organization.created"


class DomainEvent(BaseModel):
    """Immutable domain event payload routed through outbox dispatcher."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: DomainEventType
    organization_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
