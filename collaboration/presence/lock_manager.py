"""Non-blocking section lock engine preventing concurrent edit collisions."""

import logging
from datetime import datetime, UTC, timedelta
from typing import Dict, Optional, Tuple
from collaboration.schemas import SectionLock, LockState

logger = logging.getLogger("collaboration.presence.lock_manager")


class SectionLockManager:
    """Manages exclusive section-level locks with mandatory TTL auto-expiration."""

    def __init__(self):
        self._locks: Dict[Tuple[str, str], SectionLock] = (
            {}
        )  # (session_id, section_id) -> SectionLock

    async def acquire_lock(
        self,
        session_id: str,
        section_id: str,
        owner_user_id: str,
        organization_id: str = "default",
        ttl_seconds: int = 300,
    ) -> Tuple[LockState, Optional[SectionLock]]:
        key = (session_id, section_id)
        now = datetime.now(UTC)

        existing = self._locks.get(key)
        if existing:
            # Check if expired
            if now > existing.expires_at:
                logger.info(
                    f"Lock on section '{section_id}' expired; reassigning to '{owner_user_id}'"
                )
            elif existing.owner_user_id == owner_user_id:
                # Refresh lock TTL
                existing.expires_at = now + timedelta(seconds=ttl_seconds)
                return LockState.ACQUIRED, existing
            else:
                logger.warning(
                    f"Lock request on '{section_id}' rejected; owned by '{existing.owner_user_id}'"
                )
                return LockState.REJECTED, existing

        # Grant new lock
        new_lock = SectionLock(
            session_id=session_id,
            section_id=section_id,
            organization_id=organization_id,
            owner_user_id=owner_user_id,
            ttl_seconds=ttl_seconds,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        self._locks[key] = new_lock
        logger.info(
            f"Lock ACQUIRED on section '{section_id}' by '{owner_user_id}' TTL={ttl_seconds}s"
        )
        return LockState.ACQUIRED, new_lock

    async def release_lock(
        self, session_id: str, section_id: str, owner_user_id: str
    ) -> bool:
        key = (session_id, section_id)
        existing = self._locks.get(key)
        if existing and existing.owner_user_id == owner_user_id:
            del self._locks[key]
            logger.info(f"Lock RELEASED on section '{section_id}' by '{owner_user_id}'")
            return True
        return False
