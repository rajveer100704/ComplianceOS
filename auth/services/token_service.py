import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from auth.repositories.token_repository import TokenRepository
from auth.services.jwt_service import JWTService
from auth.utils import hash_refresh_token, generate_secure_token
from auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TokenReplayError,
)

logger = logging.getLogger("complianceos.auth.token_service")


def _ensure_utc(dt: datetime) -> datetime:
    """Helper to convert naive datetimes from SQLite to timezone-aware UTC datetimes."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TokenService:
    """Service handling token pair issuance, single-use refresh token rotation, and family replay revocation."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_service: Optional[JWTService] = None,
        token_repo: Optional[TokenRepository] = None,
    ):
        self.session = session
        self.jwt_service = jwt_service or JWTService()
        self.token_repo = token_repo or TokenRepository(session)

    async def issue_token_pair(
        self,
        user_id: str,
        email: str,
        role: str,
        session_id: Optional[str] = None,
        org: Optional[str] = None,
        scope: Optional[List[str]] = None,
        proof_key_thumbprint: Optional[str] = None,
        created_by_ip: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issues a new 15-minute RS256 access token and a 7-day raw refresh token in a new family."""
        # 1. Access token via JWTService
        access_token = self.jwt_service.generate_access_token(
            user_id=user_id,
            email=email,
            role=role,
            sid=session_id,
            org=org,
            scope=scope,
        )

        # 2. Raw refresh token and HMAC-SHA256 peppered hash
        raw_refresh_token = generate_secure_token(prefix="rt_")
        token_hash = hash_refresh_token(raw_refresh_token)
        token_family = str(uuid.uuid4())

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS)

        # 3. Store hashed refresh token in repository
        await self.token_repo.create_refresh_token(
            user_id=user_id,
            session_id=session_id,
            token_family=token_family,
            token_hash=token_hash,
            rotation_count=0,
            proof_key_thumbprint=proof_key_thumbprint,
            expires_at=expires_at,
            created_by_ip=created_by_ip,
            device_name=device_name,
        )

        access_exp_timestamp = now + timedelta(
            minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
        )

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "expires_at": access_exp_timestamp.isoformat(),
        }

    async def rotate_refresh_token(
        self,
        raw_refresh_token: str,
        email: str,
        role: str,
        org: Optional[str] = None,
        scope: Optional[List[str]] = None,
        proof_key_thumbprint: Optional[str] = None,
        created_by_ip: Optional[str] = None,
        device_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rotates a refresh token. Validates token, handles replay detection & grace period, and issues new pair."""
        if not raw_refresh_token or not isinstance(raw_refresh_token, str):
            raise InvalidTokenError("Refresh token must be a non-empty string.")

        token_hash = hash_refresh_token(raw_refresh_token)
        token_record = await self.token_repo.find_refresh_token_by_hash(token_hash)

        if not token_record:
            raise InvalidTokenError("Invalid refresh token.")

        now = datetime.now(timezone.utc)
        token_expires_at = _ensure_utc(token_record.expires_at)

        # 1. Expiry Check
        if token_expires_at < now:
            raise TokenExpiredError("Refresh token has expired.")

        # 2. Replay & Grace Period Check
        if token_record.is_revoked or token_record.replaced_by_token:
            # Evaluate grace period window for concurrent requests
            if token_record.last_used_at:
                last_used = _ensure_utc(token_record.last_used_at)
                seconds_since_use = (now - last_used).total_seconds()
                if seconds_since_use <= settings.AUTH_REFRESH_REPLAY_GRACE_SECONDS:
                    logger.warning(
                        f"Concurrent refresh token request within grace period ({seconds_since_use:.2f}s). "
                        f"Family: {token_record.token_family}, User: {token_record.user_id}"
                    )
                    # Issue fresh access token using existing family state
                    access_token = self.jwt_service.generate_access_token(
                        user_id=token_record.user_id,
                        email=email,
                        role=role,
                        sid=token_record.session_id,
                        org=org,
                        scope=scope,
                    )
                    access_exp = now + timedelta(
                        minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
                    )
                    return {
                        "access_token": access_token,
                        "refresh_token": raw_refresh_token,
                        "token_type": "Bearer",
                        "expires_in": settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        "expires_at": access_exp.isoformat(),
                    }

            # Out of grace period -> REPLAY DETECTED!
            revoked_count = await self.token_repo.revoke_token_family(
                token_record.token_family
            )
            logger.error(
                f"SECURITY ALERT: Refresh token replay detected! Token family '{token_record.token_family}' "
                f"for user '{token_record.user_id}' has been revoked ({revoked_count} tokens invalidated)."
            )
            # Emit security event record
            try:
                from database.services.outbox_service import OutboxService

                await OutboxService.publish_event(
                    session=self.session,
                    event_type="RefreshTokenReplayDetected",
                    payload={
                        "user_id": token_record.user_id,
                        "token_family": token_record.token_family,
                        "session_id": token_record.session_id,
                        "replayed_at": now.isoformat(),
                        "ip_address": created_by_ip,
                    },
                )
            except Exception as e:
                logger.warning(f"Could not publish outbox security event: {e}")

            raise TokenReplayError(
                "Security alert: Refresh token reuse detected. All sessions in token family have been revoked."
            )

        # 3. Successful Rotation
        new_raw_refresh_token = generate_secure_token(prefix="rt_")
        new_token_hash = hash_refresh_token(new_raw_refresh_token)

        # Mark current token used & replaced
        await self.token_repo.mark_token_used(
            token_id=token_record.id,
            replaced_by_hash=new_token_hash,
        )

        # Create rotated token in same family
        expires_at = now + timedelta(days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.token_repo.create_refresh_token(
            user_id=token_record.user_id,
            session_id=token_record.session_id,
            token_family=token_record.token_family,
            token_hash=new_token_hash,
            rotation_count=token_record.rotation_count + 1,
            proof_key_thumbprint=proof_key_thumbprint
            or token_record.proof_key_thumbprint,
            expires_at=expires_at,
            created_by_ip=created_by_ip or token_record.created_by_ip,
            device_name=device_name or token_record.device_name,
        )

        # Issue new access token
        access_token = self.jwt_service.generate_access_token(
            user_id=token_record.user_id,
            email=email,
            role=role,
            sid=token_record.session_id,
            org=org,
            scope=scope,
        )
        access_exp = now + timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)

        return {
            "access_token": access_token,
            "refresh_token": new_raw_refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "expires_at": access_exp.isoformat(),
        }

    async def revoke_token_family(self, token_family: str) -> int:
        """Revokes all refresh tokens in a given family."""
        return await self.token_repo.revoke_token_family(token_family)

    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revokes all refresh tokens for a user across all families (Logout All)."""
        return await self.token_repo.revoke_all_for_user(user_id)

    async def cleanup_expired(self) -> int:
        """Deletes expired refresh tokens from database."""
        return await self.token_repo.cleanup_expired_tokens()
