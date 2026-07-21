#!/usr/bin/env python3
"""Script to generate development RSA 2048-bit keypair for RS256 JWT signing."""

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

KEYS_DIR = Path(__file__).resolve().parent.parent / "config" / "keys"


def generate_rsa_keypair(out_dir: Path = KEYS_DIR) -> None:
    """Generates 2048-bit RSA private and public keys and saves them as PEM files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    priv_path = out_dir / "private.pem"
    pub_path = out_dir / "public.pem"

    if priv_path.exists() and pub_path.exists():
        print(f"Development RSA keys already exist at: {out_dir}")
        return

    print("Generating 2048-bit RSA keypair for development...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()

    # PEM Private Key
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    # PEM Public Key
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with open(priv_path, "wb") as f:
        f.write(priv_pem)

    with open(pub_path, "wb") as f:
        f.write(pub_pem)

    print(
        f"Successfully generated RSA keypair:\n  Private: {priv_path}\n  Public: {pub_path}"
    )


if __name__ == "__main__":
    generate_rsa_keypair()
