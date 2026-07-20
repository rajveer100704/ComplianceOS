from typing import Optional, Dict, Any, List
from fastapi import Header, HTTPException, status
from config.settings import settings
from auth.providers.api_key import APIKeyAuthProvider
from auth.providers.jwt import JWTAuthProvider

ROLE_HIERARCHY = {
    "Reviewer": 1,
    "Lead Reviewer": 2,
    "Admin": 3
}

def get_auth_provider():
    """Factory returning the active authentication provider based on settings."""
    provider_type = settings.AUTH_PROVIDER.lower()
    if provider_type == "jwt":
        return JWTAuthProvider()
    return APIKeyAuthProvider()

async def get_current_user(authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency injecting current authenticated user."""
    token = authorization or x_api_key
    
    # In development mode, if no auth header is provided, return default reviewer
    if not token and settings.ENVIRONMENT == "development":
        return {
            "sub": "dev_default_user",
            "role": "Admin",
            "provider": "development_default"
        }
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token or X-API-Key header is required"
        )
        
    provider = get_auth_provider()
    user = await provider.authenticate(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or API key"
        )
    return user

def require_role(min_role: str):
    """RBAC Guard dependency enforcing minimum role level."""
    async def role_checker(user: Dict[str, Any] = Header(None)):
        # If user dictionary is passed directly or fetched via dependency
        user_role = user.get("role", "Reviewer") if isinstance(user, dict) else "Reviewer"
        
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 3)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' lacks sufficient permissions. Required role: '{min_role}'."
            )
        return user
    return role_checker
