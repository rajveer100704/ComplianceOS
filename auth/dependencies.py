from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, Union
from fastapi import Request, Header, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from database.session import async_session_factory
from database.models.user import User
from database.models.enums import UserRole
from database.models.session_model import SessionModel
from auth.enums import Permission, ROLE_PERMISSIONS_MAP, has_permission
from auth.schemas import SecurityContext
from auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)
from auth.services.jwt_service import JWTService
from auth.repositories.user_repository import UserRepository
from auth.repositories.token_repository import TokenRepository
from auth.utils import hash_refresh_token

# Swagger UI OAuth2 Scheme for Authorize Button
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_db_session():
    """FastAPI async session dependency."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_token_from_request(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
) -> Optional[str]:
    """Extracts raw token string from OAuth2 Bearer, Authorization header, X-API-Key, or access_token cookie."""
    # 1. Bearer token from OAuth2 scheme or Authorization header
    raw_header = bearer_token or authorization
    if raw_header:
        if raw_header.startswith("Bearer "):
            return raw_header[7:].strip()
        return raw_header.strip()

    # 2. X-API-Key header
    if x_api_key:
        return x_api_key.strip()

    # 3. Cookie fallback
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.strip()

    return None


async def get_security_context(
    request: Request,
    token: Optional[str] = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db_session),
) -> SecurityContext:
    """Security translation layer validating token, loading User + Role + Permissions + Session from DB."""
    request_id = getattr(request.state, "request_id", "unknown")

    # Static API Key check (for explicit API key header or match)
    if token and settings.API_KEY and token == settings.API_KEY:
        repo = UserRepository(db)
        user = await repo.find_by_email("admin@complianceos.io")
        if not user:
            user = await repo.create_google_user(
                email="admin@complianceos.io",
                provider_user_id="static_api_key_admin",
                role=UserRole.ADMIN,
                full_name="System Admin",
            )
            await db.flush()

        perms = ROLE_PERMISSIONS_MAP.get(user.role, set())
        return SecurityContext(
            user=user,
            permissions=perms,
            token=token,
            organization_id=user.organization_id,
            request_id=request_id,
        )

    # Missing token check
    if not token:
        # Development mode fallback if no credentials sent
        if settings.ENVIRONMENT == "development":
            repo = UserRepository(db)
            user = await repo.find_by_email("dev@complianceos.io")
            if not user:
                user = await repo.create_google_user(
                    email="dev@complianceos.io",
                    provider_user_id="dev_user_default",
                    role=UserRole.REVIEWER,
                    full_name="Development User",
                )
                await db.flush()

            perms = ROLE_PERMISSIONS_MAP.get(user.role, set())
            return SecurityContext(
                user=user,
                permissions=perms,
                token="dev_fallback_token",
                organization_id=user.organization_id,
                request_id=request_id,
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # RS256 JWT Verification
    jwt_svc = JWTService()
    try:
        payload = jwt_svc.verify_access_token(token)
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id = payload.get("sub")
    session_id = payload.get("sid")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject ('sub') claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Database User Lookup
    repo = UserRepository(db)
    user = await repo.find_by_id(user_id)

    if not user or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user account does not exist or was deleted.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # User Status & Active Check
    status_str = (
        user.status.value if isinstance(user.status, Enum) else str(user.status)
    )
    if not user.is_active or status_str.lower() != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is inactive or suspended (status: {status_str}).",
        )

    # Resolve Role & Permissions
    user_role = user.role
    permissions = ROLE_PERMISSIONS_MAP.get(user_role, set())

    # Session Lookup if sid present
    session_entity: Optional[SessionModel] = None
    if session_id:
        sess_res = await db.execute(
            select(SessionModel).where(
                SessionModel.id == session_id,
                SessionModel.is_deleted.is_(False),
            )
        )
        session_entity = sess_res.scalar_one_or_none()

    return SecurityContext(
        user=user,
        permissions=permissions,
        session=session_entity,
        token=token,
        organization_id=user.organization_id,
        request_id=request_id,
    )


async def get_current_user(
    context: SecurityContext = Depends(get_security_context),
) -> User:
    """Dependency returning authenticated database User entity."""
    return context.user


async def get_current_active_user(
    context: SecurityContext = Depends(get_security_context),
) -> User:
    """Dependency returning authenticated and active database User entity."""
    return context.user


def require_permission(*required_permissions: Permission):
    """Dependency factory enforcing that the authenticated user possesses all required permissions."""

    async def permission_checker(
        context: SecurityContext = Depends(get_security_context),
    ) -> SecurityContext:
        for perm in required_permissions:
            if not has_permission(context.permissions, perm):
                perm_val = perm.value if isinstance(perm, Enum) else str(perm)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires '{perm_val}' permission.",
                )
        return context

    return permission_checker


def require_role(*allowed_roles: Union[UserRole, str]):
    """Dependency factory enforcing that the authenticated user has one of the allowed roles (Owner always allowed)."""

    async def role_checker(
        context: SecurityContext = Depends(get_security_context),
    ) -> SecurityContext:
        user_role = context.user.role
        # Owner role always has full access
        if (
            user_role == UserRole.OWNER
            or user_role.value == "Owner"
            or "Owner" in allowed_roles
        ):
            return context

        allowed_values = {
            r.value if isinstance(r, Enum) else str(r) for r in allowed_roles
        }

        if user_role.value in allowed_values or user_role in allowed_roles:
            return context

        role_names = list(allowed_values)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation requires one of the following roles: {', '.join(role_names)}.",
        )

    return role_checker
