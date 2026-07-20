from typing import Optional, Dict, Any
from config.settings import settings

class APIKeyAuthProvider:
    """API Key Authentication Provider."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.API_KEY

    async def authenticate(self, token_or_key: str) -> Optional[Dict[str, Any]]:
        """Validates API Key and returns user payload."""
        if not token_or_key:
            return None
            
        clean_key = token_or_key.replace("Bearer ", "").replace("ApiKey ", "").strip()
        if clean_key == self.api_key:
            return {
                "sub": "api_user_admin",
                "role": "Admin",
                "provider": "api_key",
                "permissions": ["read", "write", "approve", "publish", "export"]
            }
        return None
