"""Centralized CollaborationManager facade orchestrating workspaces, presence, locks, comments, and audit events."""

import logging
from typing import Dict, List, Optional, Tuple
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
from memory.manager import MemoryManager
from knowledge_graph.manager import KnowledgeGraphManager

logger = logging.getLogger("collaboration.manager")


class CollaborationManager:
    """Centralized facade serving the 3-Pane Review Workstation SPA for real-time collaboration."""

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        graph_manager: Optional[KnowledgeGraphManager] = None,
    ):
        self.workspaces: Dict[str, Workspace] = {}
        self.sessions: Dict[str, ReviewSession] = {}
        self.comment_store = CommentStore()
        self.lock_manager = SectionLockManager()
        self.presence_tracker = PresenceTracker()
        self.dispatcher = ActivityEventDispatcher(memory_manager, graph_manager)

    async def create_workspace(
        self,
        name: str,
        organization_id: str = "default",
        description: Optional[str] = None,
    ) -> Workspace:
        ws = Workspace(
            name=name, organization_id=organization_id, description=description
        )
        self.workspaces[ws.id] = ws
        logger.info(f"Created Workspace '{ws.id}' ({name})")
        return ws

    async def create_session(
        self, workspace_id: str, title: str, organization_id: str = "default"
    ) -> ReviewSession:
        sess = ReviewSession(
            workspace_id=workspace_id, title=title, organization_id=organization_id
        )
        self.sessions[sess.id] = sess
        logger.info(f"Created ReviewSession '{sess.id}' ({title})")
        return sess

    async def acquire_lock(
        self,
        session_id: str,
        section_id: str,
        user_id: str,
        organization_id: str = "default",
        ttl_seconds: int = 300,
    ) -> Tuple[LockState, Optional[SectionLock]]:
        status, lock = await self.lock_manager.acquire_lock(
            session_id, section_id, user_id, organization_id, ttl_seconds
        )
        if status == LockState.ACQUIRED:
            await self.dispatcher.dispatch(
                ActivityEvent(
                    session_id=session_id,
                    organization_id=organization_id,
                    actor_id=user_id,
                    event_type="LOCK_ACQUIRED",
                    target_entity_id=section_id,
                )
            )
        return status, lock

    async def release_lock(
        self,
        session_id: str,
        section_id: str,
        user_id: str,
        organization_id: str = "default",
    ) -> bool:
        released = await self.lock_manager.release_lock(session_id, section_id, user_id)
        if released:
            await self.dispatcher.dispatch(
                ActivityEvent(
                    session_id=session_id,
                    organization_id=organization_id,
                    actor_id=user_id,
                    event_type="LOCK_RELEASED",
                    target_entity_id=section_id,
                )
            )
        return released

    async def add_comment(
        self,
        session_id: str,
        section_id: str,
        author_id: str,
        content: str,
        organization_id: str = "default",
        parent_comment_id: Optional[str] = None,
        mentions: Optional[List[str]] = None,
    ) -> CommentThread:
        cmt = CommentThread(
            session_id=session_id,
            section_id=section_id,
            organization_id=organization_id,
            author_id=author_id,
            content=content,
            parent_comment_id=parent_comment_id,
            mentions=mentions or [],
        )
        saved = await self.comment_store.add_comment(cmt)

        await self.dispatcher.dispatch(
            ActivityEvent(
                session_id=session_id,
                organization_id=organization_id,
                actor_id=author_id,
                event_type="COMMENT_ADDED",
                target_entity_id=section_id,
                details={"mentions": saved.mentions},
            )
        )
        return saved

    async def update_presence(
        self,
        session_id: str,
        user_id: str,
        organization_id: str = "default",
        status: PresenceStatus = PresenceStatus.ONLINE,
        active_section_id: Optional[str] = None,
        cursor_offset: Optional[int] = None,
    ) -> UserPresence:
        return await self.presence_tracker.update_presence(
            session_id,
            user_id,
            organization_id,
            status,
            active_section_id,
            cursor_offset,
        )

    async def get_active_participants(
        self, session_id: str, organization_id: str = "default"
    ) -> List[UserPresence]:
        return await self.presence_tracker.get_active_participants(
            session_id, organization_id
        )

    async def get_activity_log(self, session_id: str) -> List[ActivityEvent]:
        return await self.dispatcher.get_events(session_id)
