from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Tuple
from config.settings import settings

KEYS_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "keys"


class KeyProvider(ABC):
    """Abstract interface for RSA key loading and key rotation management."""

    @abstractmethod
    def get_active_private_key(self) -> Tuple[str, str]:
        """Returns active (kid, private_key_pem) tuple for token signing."""
        pass

    @abstractmethod
    def get_public_keys(self) -> Dict[str, str]:
        """Returns dictionary mapping {kid: public_key_pem} for verification and JWKS generation."""
        pass


class FileSystemKeyProvider(KeyProvider):
    """File-system based key provider loading RSA keys from PEM files or settings."""

    def __init__(
        self,
        active_kid: str = "complianceos-key-v1",
        keys_dir: Path = KEYS_DIR,
    ):
        self.active_kid = active_kid
        self.keys_dir = keys_dir
        self._rotation_public_keys: Dict[str, str] = {}

    def add_rotation_public_key(self, kid: str, public_pem: str) -> None:
        """Register an additional public key for rotation support."""
        self._rotation_public_keys[kid] = public_pem

    def get_active_private_key(self) -> Tuple[str, str]:
        # 1. Environment setting override
        if settings.AUTH_RSA_PRIVATE_KEY:
            return (self.active_kid, settings.AUTH_RSA_PRIVATE_KEY)

        # 2. File system lookup
        priv_path = self.keys_dir / "private.pem"
        if priv_path.exists():
            return (self.active_kid, priv_path.read_text(encoding="utf-8"))

        raise FileNotFoundError(
            f"Active RSA private key not found at {priv_path}. "
            f"Run 'python scripts/generate_dev_keys.py' to generate development keys."
        )

    def get_public_keys(self) -> Dict[str, str]:
        public_keys: Dict[str, str] = {}

        # Load active public key
        if settings.AUTH_RSA_PUBLIC_KEY:
            public_keys[self.active_kid] = settings.AUTH_RSA_PUBLIC_KEY
        else:
            pub_path = self.keys_dir / "public.pem"
            if pub_path.exists():
                public_keys[self.active_kid] = pub_path.read_text(encoding="utf-8")

        # Merge rotation public keys
        public_keys.update(self._rotation_public_keys)
        return public_keys
