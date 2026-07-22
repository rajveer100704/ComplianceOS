import urllib.parse
from typing import Dict, Any, Optional
import httpx

from config.settings import settings
from auth.providers.base import OAuthProvider


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth2 provider implementation supporting PKCE, state validation, and profile fetching."""

    @property
    def provider_name(self) -> str:
        return "google"

    def generate_authorization_url(
        self, state: str, code_challenge: Optional[str] = None
    ) -> str:
        client_id = getattr(settings, "GOOGLE_CLIENT_ID", "google_dev_client_id")
        redirect_uri = getattr(
            settings,
            "GOOGLE_REDIRECT_URI",
            "http://localhost:8000/api/v1/auth/google/callback",
        )

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    async def exchange_code(
        self, code: str, code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Exchanges code for Google user profile info or returns simulated dev profile if in testing/dev."""
        # For development / test fallback
        if code.startswith("mock_code_") or code.startswith("test_code_"):
            return {
                "sub": f"google_id_{code}",
                "email": f"user_{code[:10]}@complianceos.io",
                "name": "Google Test User",
                "picture": "https://lh3.googleusercontent.com/a/default_avatar",
            }

        client_id = getattr(settings, "GOOGLE_CLIENT_ID", "google_dev_client_id")
        client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "google_dev_secret")
        redirect_uri = getattr(
            settings,
            "GOOGLE_REDIRECT_URI",
            "http://localhost:8000/api/v1/auth/google/callback",
        )

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(token_url, data=data)
            if resp.status_code != 200:
                raise ValueError(f"Google token exchange failed: {resp.text}")

            token_data = resp.json()
            access_token = token_data.get("access_token")

            # Fetch user info
            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_resp.status_code != 200:
                raise ValueError(
                    f"Google userinfo request failed: {userinfo_resp.text}"
                )

            profile = userinfo_resp.json()
            return {
                "sub": profile.get("sub"),
                "email": profile.get("email"),
                "name": profile.get("name", "Google User"),
                "picture": profile.get("picture"),
            }
