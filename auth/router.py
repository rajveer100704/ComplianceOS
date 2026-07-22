import hashlib
import json
from typing import Optional
from fastapi import APIRouter, Response, Request, HTTPException, status, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from auth.services.jwt_service import JWTService
from auth.services.auth_service import AuthService
from auth.dependencies import get_security_context, SecurityContext, get_db_session
from auth.schemas import (
    LoginResponse,
    RefreshTokenRequest,
    LogoutRequest,
    UserProfileResponse,
    TokenResponse,
)

router = APIRouter(tags=["Authentication"])
_jwt_service = JWTService()


# --- 1. JWKS Public Keys Endpoint ---


@router.get("/.well-known/jwks.json", summary="JSON Web Key Set (JWKS)")
async def get_jwks(response: Response):
    """Exposes public RSA verification keys for distributed token verification."""
    jwks_data = _jwt_service.get_jwks()
    content_bytes = json.dumps(jwks_data, sort_keys=True).encode("utf-8")

    etag = f'"{hashlib.sha256(content_bytes).hexdigest()[:16]}"'
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["ETag"] = etag

    return jwks_data


# --- 2. Google OAuth2 Login Initiation ---


@router.get(
    "/api/v1/auth/google/login",
    summary="Initiate Google OAuth2 Login Flow",
    response_model=LoginResponse,
)
async def google_login(
    response: Response,
    request: Request,
    redirect: bool = Query(
        default=True, description="Whether to return 302 redirect or JSON URL"
    ),
    code_challenge: Optional[str] = Query(
        default=None, description="PKCE code challenge S256"
    ),
    db: AsyncSession = Depends(get_db_session),
):
    """Initiates Google OAuth2 login flow with CSRF state generation and optional PKCE."""
    auth_svc = AuthService(db)
    auth_url, state = await auth_svc.initiate_google_login(
        code_challenge=code_challenge
    )
    await db.commit()

    # Set HttpOnly CSRF state cookie
    is_secure = settings.ENVIRONMENT != "development"
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/",
        max_age=600,
    )

    if redirect:
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

    return LoginResponse(authorization_url=auth_url, state=state, provider="google")


# --- 3. Google OAuth2 Callback Endpoint ---


@router.get(
    "/api/v1/auth/google/callback",
    summary="Google OAuth2 Callback Handler",
    response_model=TokenResponse,
)
async def google_callback(
    request: Request,
    response: Response,
    code: str = Query(..., description="Authorization code returned by Google"),
    state: str = Query(..., description="CSRF state parameter returned by Google"),
    db: AsyncSession = Depends(get_db_session),
):
    """Exchanges code for user profile, provisions user, creates session, and sets HttpOnly cookies."""
    expected_state = request.cookies.get("oauth_state")
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    auth_svc = AuthService(db)
    try:
        res = await auth_svc.process_google_callback(
            code=code,
            state=state,
            expected_state=expected_state,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth callback failed: {str(e)}",
        ) from e

    is_secure = settings.ENVIRONMENT != "development"

    # Access Token Cookie (Path=/)
    response.set_cookie(
        key="access_token",
        value=res["access_token"],
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/",
        max_age=res["expires_in_seconds"],
    )

    # Refresh Token Cookie (Path=/)
    response.set_cookie(
        key="refresh_token",
        value=res["refresh_token"],
        httponly=True,
        samesite="strict",
        secure=is_secure,
        path="/",
        max_age=7 * 24 * 3600,
    )

    return TokenResponse(
        access_token=res["access_token"],
        token_type="Bearer",
        expires_in_seconds=res["expires_in_seconds"],
        refresh_token=res["refresh_token"],
    )


# --- 4. Refresh Token Rotation Endpoint ---


@router.post(
    "/api/v1/auth/refresh",
    summary="Rotate Refresh Token and Issue New Token Pair",
    response_model=TokenResponse,
)
async def refresh_tokens(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Rotates single-use refresh token, detecting replay attacks and returning new token pair."""
    # Extract refresh token from Cookie -> Body -> Authorization Header
    raw_token = request.cookies.get("refresh_token")
    if not raw_token and payload and payload.refresh_token:
        raw_token = payload.refresh_token
    if not raw_token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header[7:].strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token was not provided in cookie, body, or header.",
        )

    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    auth_svc = AuthService(db)
    try:
        res = await auth_svc.refresh_tokens(
            raw_refresh_token=raw_token,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
        ) from e

    is_secure = settings.ENVIRONMENT != "development"

    response.set_cookie(
        key="access_token",
        value=res["access_token"],
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/",
        max_age=res["expires_in_seconds"],
    )

    response.set_cookie(
        key="refresh_token",
        value=res["refresh_token"],
        httponly=True,
        samesite="strict",
        secure=is_secure,
        path="/",
        max_age=7 * 24 * 3600,
    )

    return TokenResponse(
        access_token=res["access_token"],
        token_type="Bearer",
        expires_in_seconds=res["expires_in_seconds"],
        refresh_token=res["refresh_token"],
    )


# --- 5. 3-Way Logout Endpoint ---


@router.post(
    "/api/v1/auth/logout",
    summary="Revoke Session & Tokens (Logout Current, Others, or All)",
)
async def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest = LogoutRequest(scope="current"),
    context: SecurityContext = Depends(get_security_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Revokes session and refresh tokens. Supports scope: 'current', 'others', or 'all'."""
    session_id = context.session.id if context.session else None
    auth_svc = AuthService(db)

    revoked_count = await auth_svc.logout(
        user_id=context.user.id,
        current_session_id=session_id,
        scope=payload.scope,
    )
    await db.commit()

    # Clear HttpOnly auth cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return {
        "ok": True,
        "message": f"Logout completed successfully ({payload.scope} scope).",
        "scope": payload.scope,
        "revoked_count": revoked_count,
    }


# --- 6. User Profile Endpoint ---


@router.get(
    "/api/v1/auth/me",
    summary="Get Current Authenticated User Profile & Active Permissions",
    response_model=UserProfileResponse,
)
async def get_me(
    context: SecurityContext = Depends(get_security_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Returns authenticated user profile, assigned role, active permissions, and session info."""
    auth_svc = AuthService(db)
    profile = await auth_svc.build_user_profile(context)
    await db.commit()
    return profile
