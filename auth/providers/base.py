from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class OAuthProvider(ABC):
    """Abstract base class for OAuth2 authentication providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """String identifier of the OAuth provider (e.g. 'google')."""
        pass

    @abstractmethod
    def generate_authorization_url(
        self, state: str, code_challenge: Optional[str] = None
    ) -> str:
        """Generates the authorization redirect URL with CSRF state and optional PKCE challenge."""
        pass

    @abstractmethod
    async def exchange_code(
        self, code: str, code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchanges authorization code for provider user identity payload."""
        pass
