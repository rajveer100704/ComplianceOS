import logging
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from auth.repositories.token_repository import TokenRepository
from auth.devices.device_info_provider import (
    DeviceInfoProvider,
    DefaultDeviceInfoProvider,
)
from auth.utils import hash_refresh_token, generate_secure_token
from database.models.session_model import SessionModel

logger = logging.getLogger("complianceos.auth.session_service")


class SessionState(str, Enum):
    """Adaptive session state status indicator."""

    VALID = "VALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    HIGH_RISK = "HIGH_RISK"


def _ensure_utc(dt: datetime) -> datetime:
    """Helper to convert naive datetimes from SQLite to timezone-aware UTC datetimes."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class SessionService:
    """Service managing session creation, heartbeat throttling, risk scoring, device metadata, and 3-way logouts."""

    def __init__(
        self,
        session: AsyncSession,
        device_info_provider: Optional[DeviceInfoProvider] = None,
        token_repo: Optional[TokenRepository] = None,
    ):
        self.session = session
        self.device_provider = device_info_provider or DefaultDeviceInfoProvider()
        self.token_repo = token_repo or TokenRepository(session)

    async def create_session(
        self,
        user_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates and persists a new user session with dual idle/absolute timeouts and device fingerprint."""
        raw_session_token = generate_secure_token(prefix="st_")
        session_token_hash = hash_refresh_token(raw_session_token)

        device_info = self.device_provider.parse_device_info(user_agent)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.AUTH_SESSION_IDLE_EXPIRE_DAYS)

        session_entity = SessionModel(
            user_id=user_id,
            session_token_hash=session_token_hash,
            user_agent=device_info["user_agent_raw"],
            ip_address=ip_address,
            device_type=device_info["device_type"],
            browser=device_info["browser"],
            operating_system=device_info["operating_system"],
            last_activity_at=now,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
            is_deleted=False,
        )

        created_session = await self.token_repo.create_session(session_entity)

        # Emit SessionCreated event
        try:
            from database.services.outbox_service import OutboxService

            await OutboxService.publish_event(
                session=self.session,
                event_type="SessionCreated",
                payload={
                    "session_id": created_session.id,
                    "user_id": user_id,
                    "device_type": device_info["device_type"],
                    "browser": device_info["browser"],
                    "operating_system": device_info["operating_system"],
                    "ip_address": ip_address,
                    "created_at": now.isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Could not publish outbox SessionCreated event: {e}")

        return {
            "session_id": created_session.id,
            "session_token": raw_session_token,
            "user_id": user_id,
            "device_info": device_info,
            "expires_at": expires_at.isoformat(),
        }

    async def validate_session(
        self,
        session_id: str,
        user_agent: Optional[str] = None,
    ) -> Tuple[SessionState, Optional[SessionModel]]:
        """Evaluates session state (VALID, EXPIRED, REVOKED, HIGH_RISK) using dual timeouts and fingerprint check."""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if not session_obj or session_obj.is_deleted:
            return SessionState.REVOKED, None

        now = datetime.now(timezone.utc)
        created_at = _ensure_utc(session_obj.created_at)
        last_activity = _ensure_utc(session_obj.last_activity_at)

        # 1. Absolute Timeout (Hard Limit: e.g. 90 days)
        absolute_limit = created_at + timedelta(
            days=settings.AUTH_SESSION_ABSOLUTE_EXPIRE_DAYS
        )
        if now > absolute_limit:
            return SessionState.EXPIRED, session_obj

        # 2. Idle Timeout (Inactivity Limit: e.g. 30 days)
        idle_limit = last_activity + timedelta(
            days=settings.AUTH_SESSION_IDLE_EXPIRE_DAYS
        )
        if now > idle_limit:
            return SessionState.EXPIRED, session_obj

        # 3. High Risk Fingerprint Change Check
        if user_agent:
            current_info = self.device_provider.parse_device_info(user_agent)
            if (
                current_info["device_type"] != session_obj.device_type
                and current_info["device_type"] != "unknown"
                and session_obj.device_type != "unknown"
            ):
                logger.warning(
                    f"HIGH RISK SESSION DETECTED! Session {session_id} device mismatch: "
                    f"stored={session_obj.device_type}, current={current_info['device_type']}"
                )
                return SessionState.HIGH_RISK, session_obj

        return SessionState.VALID, session_obj

    async def touch_session_activity(
        self,
        session_id: str,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Updates session last_activity_at timestamp with configurable write throttling."""
        state, session_obj = await self.validate_session(
            session_id, user_agent=user_agent
        )
        if state != SessionState.VALID or not session_obj:
            return False

        now = datetime.now(timezone.utc)
        last_activity = _ensure_utc(session_obj.last_activity_at)

        # Write Throttling: Only update DB if last activity was > touch_interval ago
        elapsed = (now - last_activity).total_seconds()
        if elapsed < settings.AUTH_SESSION_TOUCH_INTERVAL_SECONDS:
            return True

        # Extend idle expiration
        new_expires_at = now + timedelta(days=settings.AUTH_SESSION_IDLE_EXPIRE_DAYS)

        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                last_activity_at=now,
                expires_at=new_expires_at,
                updated_at=now,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

        # Emit SessionTouched event
        try:
            from database.services.outbox_service import OutboxService

            await OutboxService.publish_event(
                session=self.session,
                event_type="SessionTouched",
                payload={
                    "session_id": session_id,
                    "user_id": session_obj.user_id,
                    "touched_at": now.isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"Could not publish outbox SessionTouched event: {e}")

        return True

    # --- 3-Way Logout API ---

    async def revoke_session(self, session_id: str) -> bool:
        """Revokes single session and all linked refresh tokens (Logout Current Device)."""
        success = await self.token_repo.revoke_session(session_id)
        if success:
            try:
                from database.services.outbox_service import OutboxService

                await OutboxService.publish_event(
                    session=self.session,
                    event_type="SessionRevoked",
                    payload={"session_id": session_id},
                )
            except Exception as e:
                logger.warning(f"Could not publish outbox SessionRevoked event: {e}")
        return success

    async def revoke_other_sessions(self, user_id: str, current_session_id: str) -> int:
        """Revokes all active sessions for a user EXCEPT current_session_id (Logout Other Devices)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.id != current_session_id,
                SessionModel.is_deleted.is_(False),
            )
            .values(is_deleted=True, deleted_at=now, updated_at=now)
        )
        result: Any = await self.session.execute(stmt)
        revoked_count = int(result.rowcount)
        await self.session.flush()
        return revoked_count

    async def revoke_all_sessions(self, user_id: str) -> int:
        """Revokes ALL sessions and refresh tokens for a user (Logout Everywhere)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(SessionModel)
            .where(
                SessionModel.user_id == user_id,
                SessionModel.is_deleted.is_(False),
            )
            .values(is_deleted=True, deleted_at=now, updated_at=now)
        )
        result: Any = await self.session.execute(stmt)
        count = int(result.rowcount)

        # Revoke all refresh tokens
        await self.token_repo.revoke_all_for_user(user_id)

        try:
            from database.services.outbox_service import OutboxService

            await OutboxService.publish_event(
                session=self.session,
                event_type="AllSessionsRevoked",
                payload={"user_id": user_id, "revoked_count": count},
            )
        except Exception as e:
            logger.warning(f"Could not publish outbox AllSessionsRevoked event: {e}")

        return count

    # --- Active Session Listing & Cleanup ---

    async def get_user_sessions(
        self,
        user_id: str,
        current_session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns structured active session list for Active Devices UI."""
        active_sessions = await self.token_repo.list_active_by_user(user_id)
        result_list = []

        for s in active_sessions:
            result_list.append(
                {
                    "session_id": s.id,
                    "user_id": s.user_id,
                    "device_type": s.device_type,
                    "browser": s.browser,
                    "operating_system": s.operating_system,
                    "ip_address": s.ip_address,
                    "country": s.country,
                    "city": s.city,
                    "last_activity_at": _ensure_utc(s.last_activity_at).isoformat(),
                    "created_at": _ensure_utc(s.created_at).isoformat(),
                    "expires_at": _ensure_utc(s.expires_at).isoformat(),
                    "is_current": (
                        s.id == current_session_id if current_session_id else False
                    ),
                }
            )
        return result_list

    async def cleanup_expired_sessions(self) -> int:
        """Deletes expired sessions past absolute limit or idle limit."""
        now = datetime.now(timezone.utc)
        stmt = delete(SessionModel).where(SessionModel.expires_at < now)
        result: Any = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount)

    async def cleanup_revoked_sessions(self) -> int:
        """Deletes soft-deleted/revoked sessions from database."""
        stmt = delete(SessionModel).where(SessionModel.is_deleted.is_(True))
        result: Any = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount)
