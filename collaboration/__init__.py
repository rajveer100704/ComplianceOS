"""Real-Time Collaboration & Workspace Workstation package for v2.0 AI Platform."""

from collaboration.schemas import (
    Workspace,
    ReviewSession,
    SectionLock,
    CommentThread,
    UserPresence,
    ActivityEvent,
    PresenceStatus,
    LockState,
)
from collaboration.comments.store import CommentStore
from collaboration.presence.lock_manager import SectionLockManager
from collaboration.presence.tracker import PresenceTracker
from collaboration.webhooks.dispatcher import ActivityEventDispatcher
from collaboration.manager import CollaborationManager

__all__ = [
    "Workspace",
    "ReviewSession",
    "SectionLock",
    "CommentThread",
    "UserPresence",
    "ActivityEvent",
    "PresenceStatus",
    "LockState",
    "CommentStore",
    "SectionLockManager",
    "PresenceTracker",
    "ActivityEventDispatcher",
    "CollaborationManager",
]
