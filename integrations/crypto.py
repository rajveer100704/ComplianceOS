import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from config.settings import settings

logger = logging.getLogger("integrations_crypto")


class CredentialService:
    """Symmetric AES-256 Fernet encryption service for securing integration secrets and tokens at rest."""

    _fernet: Optional[Fernet] = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            raw_key = getattr(settings, "ENCRYPTION_KEY", None)
            if not raw_key:
                # Deterministic fallback key for development / testing
                logger.warning(
                    "ENCRYPTION_KEY not configured in settings. Using local development key fallback."
                )
                raw_key = base64.urlsafe_b64encode(
                    b"ComplianceOS_AES256_DevelopmentSecretKey_32bytes!"[:32]
                ).decode("utf-8")

            if isinstance(raw_key, str):
                key_bytes = raw_key.encode("utf-8")
            else:
                key_bytes = raw_key

            # Ensure valid Fernet base64 key format
            try:
                cls._fernet = Fernet(key_bytes)
            except Exception:
                # If raw string is not urlsafe base64, generate valid base64 key from bytes
                padded = (key_bytes + b"=" * 32)[:32]
                valid_key = base64.urlsafe_b64encode(padded)
                cls._fernet = Fernet(valid_key)

        return cls._fernet

    @classmethod
    def encrypt(cls, plaintext: Optional[str]) -> Optional[str]:
        """Encrypts plaintext secret into URL-safe Fernet ciphertext."""
        if not plaintext:
            return None
        fernet = cls._get_fernet()
        ciphertext_bytes = fernet.encrypt(plaintext.encode("utf-8"))
        return ciphertext_bytes.decode("utf-8")

    @classmethod
    def decrypt(cls, ciphertext: Optional[str]) -> Optional[str]:
        """Decrypts Fernet ciphertext back to plaintext secret."""
        if not ciphertext:
            return None
        try:
            fernet = cls._get_fernet()
            plaintext_bytes = fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to decrypt integration secret: {str(e)}")
            raise ValueError(
                "Decryption failed. Invalid key or tampered ciphertext."
            ) from e
