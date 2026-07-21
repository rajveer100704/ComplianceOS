from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from config.settings import settings
from auth.providers.api_key import APIKeyAuthProvider
from auth.providers.jwt import JWTAuthProvider

ROLE_HIERARCHY = {"Reviewer": 1, "Lead Reviewer": 2, "Admin": 3}


def get_auth_provider():
    """Factory returning the active authentication provider based on settings."""
    provider_type = settings.AUTH_PROVIDER.lower()
    if provider_type == "jwt":
        return JWTAuthProvider()
    return APIKeyAuthProvider()


async def get_current_user(
    authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Dependency injecting current authenticated user."""
    token = authorization or x_api_key

    # In development mode, if no auth header is provided, return default reviewer
    if not token and settings.ENVIRONMENT == "development":
        return {
            "sub": "dev_user_01",
            "role": "Reviewer",
            "provider": "dev_default",
        }

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    provider = get_auth_provider()
    user_payload = await provider.authenticate(token)

    if not user_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_payload


def require_role(min_role: str):
    """Dependency factory enforcing minimum required role in role hierarchy."""

    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "Reviewer")
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 99)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{min_role}' role or higher.",
            )
        return user

    return role_checker
