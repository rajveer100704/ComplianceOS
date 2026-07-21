import uuid
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from auth.keys.key_provider import KeyProvider, FileSystemKeyProvider
from auth.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TokenNotYetValidError,
    InvalidIssuerError,
    InvalidAudienceError,
    InvalidSignatureError,
    UnsupportedAlgorithmError,
    MissingClaimError,
    UnknownKeyIdError,
)

DEFAULT_ISSUER = "complianceos"
DEFAULT_AUDIENCE = "complianceos-app"
DEFAULT_ALGORITHM = "RS256"
REQUIRED_CLAIMS = ["sub", "iss", "aud", "iat", "nbf", "exp", "jti"]


def int_to_base64url(val: int) -> str:
    """Converts a large integer (like RSA modulus or exponent) to URL-safe base64 string without padding."""
    b = val.to_bytes((val.bit_length() + 7) // 8, byteorder="big")
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


class JWTService:
    """Pure Python cryptographic service for RS256 JWT signing, validation, and JWKS generation."""

    def __init__(
        self,
        key_provider: Optional[KeyProvider] = None,
        issuer: str = DEFAULT_ISSUER,
        audience: str = DEFAULT_AUDIENCE,
        algorithm: str = DEFAULT_ALGORITHM,
        access_token_expire_minutes: int = 15,
        leeway_seconds: int = 30,
    ):
        self.key_provider = key_provider or FileSystemKeyProvider()
        self.issuer = issuer
        self.audience = audience
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.leeway_seconds = leeway_seconds

    def generate_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        sid: Optional[str] = None,
        org: Optional[str] = None,
        status: str = "active",
        scope: Optional[List[str]] = None,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates an RS256 signed JWT access token with full schema claims."""
        kid, private_pem = self.key_provider.get_active_private_key()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)

        payload: Dict[str, Any] = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": str(uuid.uuid4()),
            "ver": "1.0",
            "sid": sid,
            "status": status,
            "org": org,
            "scope": scope or [],
        }
        if extra_claims:
            payload.update(extra_claims)

        headers = {
            "alg": self.algorithm,
            "kid": kid,
            "typ": "JWT",
        }

        return jwt.encode(
            payload, private_pem, algorithm=self.algorithm, headers=headers
        )

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Validates an RS256 JWT access token and returns decoded payload claims."""
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Authentication token must be a non-empty string.")

        clean_token = token.replace("Bearer ", "").strip()
        if not clean_token:
            raise InvalidTokenError("Token string is empty.")

        # 1. Unverified header inspection to extract kid and algorithm
        try:
            unverified_header = jwt.get_unverified_header(clean_token)
        except Exception as e:
            raise InvalidTokenError(f"Malformed JWT header: {str(e)}") from e

        token_alg = unverified_header.get("alg")
        if token_alg != self.algorithm:
            raise UnsupportedAlgorithmError(
                f"Token algorithm '{token_alg}' is unsupported. Only '{self.algorithm}' is allowed."
            )

        kid = unverified_header.get("kid")
        if not kid:
            raise UnknownKeyIdError("JWT header missing 'kid' key identifier.")

        public_keys = self.key_provider.get_public_keys()
        public_pem = public_keys.get(kid)
        if not public_pem:
            raise UnknownKeyIdError(
                f"Public key for key ID '{kid}' not found in key provider."
            )

        # 2. Decode & verify signature + exp + nbf + iss + aud
        try:
            payload = jwt.decode(
                clean_token,
                public_pem,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway_seconds,
                options={
                    "require": REQUIRED_CLAIMS,
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True,
                },
            )
            return payload

        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError("Access token has expired.") from e
        except jwt.ImmatureSignatureError as e:
            raise TokenNotYetValidError(
                "Access token is not yet valid (nbf in future)."
            ) from e
        except jwt.InvalidIssuerError as e:
            raise InvalidIssuerError("Token issuer claim ('iss') mismatch.") from e
        except jwt.InvalidAudienceError as e:
            raise InvalidAudienceError("Token audience claim ('aud') mismatch.") from e
        except jwt.MissingRequiredClaimError as e:
            raise MissingClaimError(f"Missing required JWT claim: {str(e)}") from e
        except jwt.InvalidSignatureError as e:
            raise InvalidSignatureError("Signature verification failed.") from e
        except jwt.PyJWTError as e:
            raise InvalidTokenError(f"Invalid access token: {str(e)}") from e

    def get_jwks(self) -> Dict[str, List[Dict[str, str]]]:
        """Generates RFC 7517 compliant JSON Web Key Set (JWKS) containing all active & rotation public keys."""
        public_keys = self.key_provider.get_public_keys()
        keys_list: List[Dict[str, str]] = []

        for kid, public_pem in public_keys.items():
            pub_key_obj = serialization.load_pem_public_key(public_pem.encode("utf-8"))
            if not isinstance(pub_key_obj, rsa.RSAPublicKey):
                continue

            numbers = pub_key_obj.public_numbers()
            n_b64 = int_to_base64url(numbers.n)
            e_b64 = int_to_base64url(numbers.e)

            keys_list.append(
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": self.algorithm,
                    "kid": kid,
                    "n": n_b64,
                    "e": e_b64,
                }
            )

        return {"keys": keys_list}
