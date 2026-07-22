import logging
import secrets
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from auth.providers.google import GoogleOAuthProvider
from auth.services.jwt_service import JWTService
from auth.services.token_service import TokenService
from auth.services.session_service import SessionService
from auth.repositories.user_repository import UserRepository
from auth.dependencies import SecurityContext
from auth.enums import ROLE_PERMISSIONS_MAP
from auth.schemas import UserProfileResponse, SessionInfoDTO, TokenResponse
from auth.exceptions import AuthError, InvalidTokenError, InsufficientPrivilegesError
from database.models.enums import UserRole, UserStatus
from database.events import EventPublisher

logger = logging.getLogger("complianceos.auth.auth_service")


class AuthService:
    """High-level authentication orchestration service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.jwt_service = JWTService()
        self.token_service = TokenService(session)
        self.session_service = SessionService(session)
        self.google_provider = GoogleOAuthProvider()

    async def initiate_google_login(
        self, code_challenge: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generates CSRF state and returns (authorization_url, state)."""
        state = f"st_{secrets.token_urlsafe(24)}"

        # Emit LoginStarted outbox event
        try:
            await EventPublisher.publish_event(
                event_type="LoginStarted",
                payload={"provider": "google", "state": state},
                session=self.session,
            )
        except Exception as e:
            logger.warning(f"Could not publish LoginStarted event: {e}")

        url = self.google_provider.generate_authorization_url(
            state=state, code_challenge=code_challenge
        )
        return url, state

    async def process_google_callback(
        self,
        code: str,
        state: str,
        expected_state: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validates CSRF state, exchanges code for profile, provisions user, creates session, and issues tokens."""
        # 1. State Validation Check
        if expected_state and state != expected_state:
            raise AuthError(
                "Invalid or mismatched OAuth state parameter (CSRF protection failed)"
            )

        # 2. Exchange code for Google Profile
        profile = await self.google_provider.exchange_code(code)
        email = profile["email"]
        provider_user_id = profile["sub"]
        full_name = profile.get("name", "Google User")
        avatar_url = profile.get("picture")

        # 3. User Lookup or Provisioning
        user = await self.user_repo.find_by_email(email)
        if not user:
            user = await self.user_repo.create_google_user(
                email=email,
                full_name=full_name,
                provider_user_id=provider_user_id,
                avatar_url=avatar_url,
            )
            # Create personal organization & owner membership for new user
            from organizations.service import OrganizationService
            org_svc = OrganizationService(self.session)
            await org_svc.create_organization(
                name=f"{full_name}'s Organization",
                creator=user,
            )
        else:
            # Record login activity
            await self.user_repo.record_login(user.id)

        # 4. Create Session
        sess_data = await self.session_service.create_session(
            user_id=user.id,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        # 5. Issue Token Pair
        from database.repositories.membership_repository import OrganizationMembershipRepository
        mem_repo = OrganizationMembershipRepository(self.session)
        memberships = await mem_repo.list_members_for_user(user.id)
        active_mem = memberships[0] if memberships else None
        role_str = active_mem.role.value if active_mem else "reviewer"
        org_id_str = active_mem.organization_id if active_mem else None

        token_pair = await self.token_service.issue_token_pair(
            user_id=user.id,
            email=user.email,
            role=role_str,
            session_id=sess_data["session_id"],
            org=org_id_str,
            created_by_ip=ip_address,
        )

        # Emit OAuthCallbackSucceeded outbox event
        try:
            await EventPublisher.publish_event(
                event_type="OAuthCallbackSucceeded",
                payload={
                    "user_id": user.id,
                    "email": user.email,
                    "session_id": sess_data["session_id"],
                    "provider": "google",
                },
                session=self.session,
            )
        except Exception as e:
            logger.warning(f"Could not publish OAuthCallbackSucceeded event: {e}")

        expires_in = (
            token_pair.get("expires_in") or token_pair.get("expires_in_seconds") or 900
        )
        return {
            "user": user,
            "session_id": sess_data["session_id"],
            "access_token": token_pair["access_token"],
            "refresh_token": token_pair["refresh_token"],
            "expires_in_seconds": expires_in,
        }

    async def refresh_tokens(
        self,
        raw_refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Rotates refresh token and returns new token pair."""
        token_pair = await self.token_service.rotate_refresh_token(
            raw_refresh_token=raw_refresh_token,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        # Emit RefreshRotated outbox event
        try:
            await EventPublisher.publish_event(
                event_type="RefreshRotated",
                payload={"session_id": token_pair.get("session_id")},
                session=self.session,
            )
        except Exception as e:
            logger.warning(f"Could not publish RefreshRotated event: {e}")

        expires_in = (
            token_pair.get("expires_in") or token_pair.get("expires_in_seconds") or 900
        )
        return {
            "access_token": token_pair["access_token"],
            "refresh_token": token_pair["refresh_token"],
            "expires_in_seconds": expires_in,
        }

    async def logout(
        self,
        user_id: str,
        current_session_id: Optional[str] = None,
        scope: str = "current",
    ) -> int:
        """Executes 3-way logout (current, others, or all)."""
        revoked_count = 0
        if scope == "others" and current_session_id:
            revoked_count = await self.session_service.revoke_other_sessions(
                user_id=user_id,
                current_session_id=current_session_id,
            )
            event_name = "LogoutOthers"
        elif scope == "all":
            revoked_count = await self.session_service.revoke_all_sessions(
                user_id=user_id
            )
            event_name = "LogoutAll"
        else:
            if current_session_id:
                success = await self.session_service.revoke_session(current_session_id)
                revoked_count = 1 if success else 0
            event_name = "LogoutCurrent"

        try:
            await EventPublisher.publish_event(
                event_type=event_name,
                payload={"user_id": user_id, "revoked_count": revoked_count},
                session=self.session,
            )
        except Exception as e:
            logger.warning(f"Could not publish logout outbox event: {e}")

        return revoked_count

    async def build_user_profile(self, context: SecurityContext) -> UserProfileResponse:
        """Builds comprehensive UserProfileResponse from SecurityContext."""
        u = context.user
        perms = [
            p.value if hasattr(p, "value") else str(p) for p in context.permissions
        ]

        current_sess_dto: Optional[SessionInfoDTO] = None
        if context.session:
            s = context.session
            current_sess_dto = SessionInfoDTO(
                session_id=s.id,
                device_type=s.device_type,
                browser=s.browser,
                operating_system=s.operating_system,
                ip_address=s.ip_address,
                last_activity_at=s.last_activity_at.isoformat(),
                created_at=s.created_at.isoformat(),
                expires_at=s.expires_at.isoformat(),
                is_current=True,
            )

        # Emit ProfileViewed outbox event
        try:
            await EventPublisher.publish_event(
                event_type="ProfileViewed",
                payload={"user_id": u.id},
                session=self.session,
            )
        except Exception as e:
            logger.warning(f"Could not publish ProfileViewed event: {e}")

        mem_role_str = (
            context.membership.role.value
            if context.membership and hasattr(context.membership.role, "value")
            else str(context.membership.role) if context.membership else "reviewer"
        )

        return UserProfileResponse(
            id=u.id,
            email=u.email,
            email_verified=u.email_verified,
            full_name=u.full_name,
            avatar_url=u.avatar_url,
            role=mem_role_str,
            status=u.status.value if hasattr(u.status, "value") else str(u.status),
            organization_id=context.organization_id,
            permissions=perms,
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
            login_count=u.login_count,
            current_session=current_sess_dto,
        )
