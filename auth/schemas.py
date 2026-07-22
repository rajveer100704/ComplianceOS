from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from typing import List, Optional, Set, TYPE_CHECKING
from database.models.user import User
from database.models.session_model import SessionModel
from auth.enums import Permission

if TYPE_CHECKING:
    from database.models.membership import OrganizationMembership
    from database.models.organization import Organization


@dataclass
class SecurityContext:
    """Enterprise security context injected into FastAPI endpoint handlers."""

    user: User
    permissions: Set[Permission] = field(default_factory=set)
    session: Optional[SessionModel] = None
    membership: Optional["OrganizationMembership"] = None
    organization: Optional["Organization"] = None
    token: str = ""
    organization_id: Optional[str] = None
    request_id: str = "unknown"


class LoginResponse(BaseModel):
    """OAuth login initiation payload."""

    authorization_url: str
    state: str
    provider: str = "google"


class RefreshTokenRequest(BaseModel):
    """Token refresh request payload."""

    refresh_token: Optional[str] = Field(
        default=None,
        description="Raw refresh token string if not provided in HttpOnly cookie",
    )


class LogoutRequest(BaseModel):
    """3-Way logout request payload."""

    scope: str = Field(
        default="current",
        description="Revocation scope: 'current', 'others', or 'all'",
    )


class SessionInfoDTO(BaseModel):
    """Active session metadata DTO for user profile."""

    session_id: str
    device_type: str
    browser: str
    operating_system: str
    ip_address: Optional[str] = None
    last_activity_at: str
    created_at: str
    expires_at: str
    is_current: bool = False


class UserProfileResponse(BaseModel):
    """Comprehensive user profile DTO returned by /me endpoint."""

    id: str
    email: str
    email_verified: bool
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    status: str
    organization_id: Optional[str] = None
    permissions: List[str]
    last_login_at: Optional[str] = None
    login_count: int = 0
    current_session: Optional[SessionInfoDTO] = None


class TokenResponse(BaseModel):
    """OAuth access and refresh token pair DTO."""

    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    refresh_token: Optional[str] = None
