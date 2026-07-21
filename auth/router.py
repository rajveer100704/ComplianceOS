import hashlib
import json
from fastapi import APIRouter, Response
from auth.services.jwt_service import JWTService

router = APIRouter(tags=["Authentication"])
_jwt_service = JWTService()


@router.get("/.well-known/jwks.json", summary="JSON Web Key Set (JWKS)")
async def get_jwks(response: Response):
    """Exposes public RSA verification keys for distributed token verification."""
    jwks_data = _jwt_service.get_jwks()
    content_bytes = json.dumps(jwks_data, sort_keys=True).encode("utf-8")

    # Deterministic ETag hash based on current JWKS payload
    etag = f'"{hashlib.sha256(content_bytes).hexdigest()[:16]}"'

    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["ETag"] = etag

    return jwks_data
