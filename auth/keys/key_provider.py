from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

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
    """File-system based key provider with environment override, file lookup, and ephemeral fallback."""

    def __init__(
        self,
        active_kid: str = "complianceos-key-v1",
        keys_dir: Path = KEYS_DIR,
    ):
        self.active_kid = active_kid
        self.keys_dir = keys_dir
        self._rotation_public_keys: Dict[str, str] = {}
        self._ephemeral_private_pem: Optional[str] = None
        self._ephemeral_public_pem: Optional[str] = None

    def add_rotation_public_key(self, kid: str, public_pem: str) -> None:
        """Register an additional public key for rotation support."""
        self._rotation_public_keys[kid] = public_pem

    def _ensure_ephemeral_keys(self) -> None:
        """Generates in-memory ephemeral 2048-bit RSA keypair fallback."""
        if not self._ephemeral_private_pem or not self._ephemeral_public_pem:
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            self._ephemeral_private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")
            self._ephemeral_public_pem = (
                private_key.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode("utf-8")
            )

    def get_active_private_key(self) -> Tuple[str, str]:
        # 1. Environment setting override
        if settings.AUTH_RSA_PRIVATE_KEY:
            return (self.active_kid, settings.AUTH_RSA_PRIVATE_KEY)

        # 2. File system lookup
        priv_path = self.keys_dir / "private.pem"
        if priv_path.exists():
            return (self.active_kid, priv_path.read_text(encoding="utf-8"))

        # 3. Ephemeral in-memory fallback (for CI & testing environments)
        self._ensure_ephemeral_keys()
        assert self._ephemeral_private_pem is not None
        return (self.active_kid, self._ephemeral_private_pem)

    def get_public_keys(self) -> Dict[str, str]:
        public_keys: Dict[str, str] = {}

        # 1. Environment setting override
        if settings.AUTH_RSA_PUBLIC_KEY:
            public_keys[self.active_kid] = settings.AUTH_RSA_PUBLIC_KEY
        else:
            # 2. File system lookup
            pub_path = self.keys_dir / "public.pem"
            if pub_path.exists():
                public_keys[self.active_kid] = pub_path.read_text(encoding="utf-8")
            else:
                # 3. Ephemeral in-memory fallback
                self._ensure_ephemeral_keys()
                assert self._ephemeral_public_pem is not None
                public_keys[self.active_kid] = self._ephemeral_public_pem

        # Merge rotation public keys
        public_keys.update(self._rotation_public_keys)
        return public_keys
