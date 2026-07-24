"""Canonical DTOs and models for Real-Time Collaboration & Workspace Workstation (Sprint 5)."""

import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PresenceStatus(str, Enum):
    ONLINE = "ONLINE"
    IDLE = "IDLE"
    OFFLINE = "OFFLINE"


class LockState(str, Enum):
    ACQUIRED = "ACQUIRED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"


class Workspace(BaseModel):
    """Organizational container holding review sessions."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: f"ws-{uuid.uuid4().hex[:8]}")
    organization_id: str = "default"
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReviewSession(BaseModel):
    """Active collaborative review workstation session instance."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: f"sess-{uuid.uuid4().hex[:8]}")
    workspace_id: str
    organization_id: str = "default"
    title: str
    active_participant_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SectionLock(BaseModel):
    """Exclusive concurrency section lock."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: f"lock-{uuid.uuid4().hex[:8]}")
    session_id: str
    section_id: str
    organization_id: str = "default"
    owner_user_id: str
    ttl_seconds: int = 300
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def compute_expiry(self) -> "SectionLock":
        if self.created_at and not self.expires_at:
            from datetime import timedelta

            self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)
        return self


class CommentThread(BaseModel):
    """Threaded reviewer comment with highlight offsets and @mentions."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: f"cmt-{uuid.uuid4().hex[:8]}")
    session_id: str
    section_id: str
    organization_id: str = "default"
    author_id: str
    content: str
    parent_comment_id: Optional[str] = None
    highlight_offset_start: Optional[int] = None
    highlight_offset_end: Optional[int] = None
    mentions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserPresence(BaseModel):
    """Participant online presence and active cursor state."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    session_id: str
    organization_id: str = "default"
    status: PresenceStatus = PresenceStatus.ONLINE
    active_section_id: Optional[str] = None
    cursor_offset: Optional[int] = None
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActivityEvent(BaseModel):
    """Audit activity event entry emitted to Memory and Knowledge Graph."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: f"act-{uuid.uuid4().hex[:8]}")
    session_id: str
    organization_id: str = "default"
    actor_id: str
    event_type: str  # e.g. LOCK_ACQUIRED, COMMENT_ADDED, APPROVAL_SUBMITTED
    target_entity_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
