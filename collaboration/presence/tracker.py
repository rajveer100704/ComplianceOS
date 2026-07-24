"""Heartbeat-based user presence and active cursor position tracker."""

import logging
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Tuple
from collaboration.schemas import UserPresence, PresenceStatus

logger = logging.getLogger("collaboration.presence.tracker")


class PresenceTracker:
    """Tracks active online participants, heartbeats, and live cursor offsets."""

    def __init__(self):
        self._presence: Dict[Tuple[str, str], UserPresence] = (
            {}
        )  # (session_id, user_id) -> UserPresence

    async def update_presence(
        self,
        session_id: str,
        user_id: str,
        organization_id: str = "default",
        status: PresenceStatus = PresenceStatus.ONLINE,
        active_section_id: str = None,
        cursor_offset: int = None,
    ) -> UserPresence:
        key = (session_id, user_id)
        now = datetime.now(UTC)

        presence = UserPresence(
            user_id=user_id,
            session_id=session_id,
            organization_id=organization_id,
            status=status,
            active_section_id=active_section_id,
            cursor_offset=cursor_offset,
            last_heartbeat=now,
        )
        self._presence[key] = presence
        return presence

    async def get_active_participants(
        self,
        session_id: str,
        organization_id: str = "default",
        timeout_seconds: int = 30,
    ) -> List[UserPresence]:
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=timeout_seconds)

        active: List[UserPresence] = []
        for p in self._presence.values():
            if p.session_id == session_id and p.organization_id == organization_id:
                if p.last_heartbeat >= cutoff and p.status != PresenceStatus.OFFLINE:
                    active.append(p)
                else:
                    p.status = PresenceStatus.OFFLINE

        return active
