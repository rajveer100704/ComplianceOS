import hmac
import hashlib
import secrets
from config.settings import settings


def hash_refresh_token(raw_token: str) -> str:
    """Computes a peppered HMAC-SHA256 hex digest of a raw refresh token using server AUTH_SECRET."""
    if not raw_token or not isinstance(raw_token, str):
        raise ValueError("Raw token must be a non-empty string.")

    clean_token = raw_token.strip()
    return hmac.new(
        settings.AUTH_SECRET.encode("utf-8"),
        clean_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_secure_token(prefix: str = "rt_") -> str:
    """Generates a cryptographically secure 256-bit random hex string token with optional prefix."""
    random_bytes = secrets.token_hex(32)
    return f"{prefix}{random_bytes}"
