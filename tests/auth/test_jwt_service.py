import pytest
import time
import jwt

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from auth.services.jwt_service import JWTService
from auth.keys.key_provider import FileSystemKeyProvider
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


@pytest.fixture
def jwt_service():
    """Provides a JWTService configured with development RSA keys."""
    return JWTService()


def test_rs256_access_token_generation_and_verification(jwt_service):
    """Test generating a valid RS256 JWT access token and verifying decoded claims."""
    token = jwt_service.generate_access_token(
        user_id="usr_12345",
        email="test@complianceos.io",
        role="Lead Reviewer",
        sid="sess_999",
        org="org_compliance_corp",
        scope=["claims:write", "reports:read"],
    )
    assert isinstance(token, str)

    payload = jwt_service.verify_access_token(token)
    assert payload["sub"] == "usr_12345"
    assert payload["email"] == "test@complianceos.io"
    assert payload["role"] == "Lead Reviewer"
    assert payload["sid"] == "sess_999"
    assert payload["org"] == "org_compliance_corp"
    assert payload["scope"] == ["claims:write", "reports:read"]
    assert payload["iss"] == "complianceos"
    assert payload["aud"] == "complianceos-app"
    assert payload["ver"] == "1.0"
    assert "jti" in payload
    assert "nbf" in payload
    assert "exp" in payload


def test_expired_token_raises_token_expired_error():
    """Test that expired tokens raise TokenExpiredError."""
    service = JWTService(access_token_expire_minutes=-5)
    token = service.generate_access_token(
        user_id="usr_exp",
        email="exp@complianceos.io",
        role="Reviewer",
    )
    with pytest.raises(TokenExpiredError):
        service.verify_access_token(token)


def test_future_nbf_raises_token_not_yet_valid_error(jwt_service):
    """Test that tokens with nbf set in the future raise TokenNotYetValidError."""
    kid, private_pem = jwt_service.key_provider.get_active_private_key()
    future_nbf = int(time.time()) + 3600
    expire = future_nbf + 900

    payload = {
        "sub": "usr_future",
        "email": "future@complianceos.io",
        "role": "Reviewer",
        "iss": "complianceos",
        "aud": "complianceos-app",
        "iat": int(time.time()),
        "nbf": future_nbf,
        "exp": expire,
        "jti": "jti_future_123",
    }
    headers = {"alg": "RS256", "kid": kid, "typ": "JWT"}
    token = jwt.encode(payload, private_pem, algorithm="RS256", headers=headers)

    with pytest.raises(TokenNotYetValidError):
        jwt_service.verify_access_token(token)


def test_invalid_issuer_raises_invalid_issuer_error(jwt_service):
    """Test that tokens signed with an un-expected issuer raise InvalidIssuerError."""
    service_evil = JWTService(issuer="evil-hacker-corp")
    token = service_evil.generate_access_token(
        user_id="usr_evil",
        email="evil@complianceos.io",
        role="Admin",
    )
    with pytest.raises(InvalidIssuerError):
        jwt_service.verify_access_token(token)


def test_invalid_audience_raises_invalid_audience_error(jwt_service):
    """Test that tokens signed with an un-expected audience raise InvalidAudienceError."""
    service_evil = JWTService(audience="other-app")
    token = service_evil.generate_access_token(
        user_id="usr_aud",
        email="aud@complianceos.io",
        role="Admin",
    )
    with pytest.raises(InvalidAudienceError):
        jwt_service.verify_access_token(token)


def test_missing_required_claim_raises_missing_claim_error(jwt_service):
    """Test that tokens missing a required claim (e.g. jti) raise MissingClaimError."""
    kid, private_pem = jwt_service.key_provider.get_active_private_key()
    now = int(time.time())

    payload = {
        "sub": "usr_noclaim",
        "email": "noclaim@complianceos.io",
        "role": "Reviewer",
        "iss": "complianceos",
        "aud": "complianceos-app",
        "iat": now,
        "nbf": now,
        "exp": now + 900,
        # Missing 'jti'
    }
    headers = {"alg": "RS256", "kid": kid, "typ": "JWT"}
    token = jwt.encode(payload, private_pem, algorithm="RS256", headers=headers)

    with pytest.raises(MissingClaimError):
        jwt_service.verify_access_token(token)


def test_unsupported_algorithm_raises_error(jwt_service):
    """Test that tokens using HS256 or none algorithm raise UnsupportedAlgorithmError."""
    payload = {
        "sub": "usr_hs256",
        "email": "hs256@complianceos.io",
        "role": "Reviewer",
        "iss": "complianceos",
        "aud": "complianceos-app",
        "iat": int(time.time()),
        "nbf": int(time.time()),
        "exp": int(time.time()) + 900,
        "jti": "jti_hs256_123",
    }
    headers = {"alg": "HS256", "kid": "complianceos-key-v1", "typ": "JWT"}
    token = jwt.encode(
        payload,
        "secret_symmetric_key_32bytes_minimum_length_for_sha256",
        algorithm="HS256",
        headers=headers,
    )

    with pytest.raises(UnsupportedAlgorithmError):
        jwt_service.verify_access_token(token)


def test_unknown_kid_raises_unknown_key_id_error(jwt_service):
    """Test that tokens with an unknown kid header raise UnknownKeyIdError."""
    kid, private_pem = jwt_service.key_provider.get_active_private_key()
    now = int(time.time())

    payload = {
        "sub": "usr_unk_kid",
        "email": "unk_kid@complianceos.io",
        "role": "Reviewer",
        "iss": "complianceos",
        "aud": "complianceos-app",
        "iat": now,
        "nbf": now,
        "exp": now + 900,
        "jti": "jti_unk_123",
    }
    headers = {"alg": "RS256", "kid": "unknown-key-id-9999", "typ": "JWT"}
    token = jwt.encode(payload, private_pem, algorithm="RS256", headers=headers)

    with pytest.raises(UnknownKeyIdError):
        jwt_service.verify_access_token(token)


def test_tampered_signature_raises_invalid_signature_error(jwt_service):
    """Test that modifying token signature payload raises InvalidSignatureError."""
    token = jwt_service.generate_access_token(
        user_id="usr_tamper",
        email="tamper@complianceos.io",
        role="Reviewer",
    )
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.invalid_signature_part"

    with pytest.raises(InvalidSignatureError):
        jwt_service.verify_access_token(tampered_token)


def test_malformed_token_input_raises_invalid_token_error(jwt_service):
    """Test that malformed or empty token strings raise InvalidTokenError."""
    with pytest.raises(InvalidTokenError):
        jwt_service.verify_access_token("")

    with pytest.raises(InvalidTokenError):
        jwt_service.verify_access_token("not.a.valid.jwt.string")


def test_jwks_export_array_format(jwt_service):
    """Test that JWKS export matches RFC 7517 compliant keys array format."""
    jwks = jwt_service.get_jwks()
    assert "keys" in jwks
    assert isinstance(jwks["keys"], list)
    assert len(jwks["keys"]) >= 1

    key_entry = jwks["keys"][0]
    assert key_entry["kty"] == "RSA"
    assert key_entry["use"] == "sig"
    assert key_entry["alg"] == "RS256"
    assert key_entry["kid"] == "complianceos-key-v1"
    assert isinstance(key_entry["n"], str)
    assert isinstance(key_entry["e"], str)


def test_jwks_key_rotation_multiple_keys():
    """Test key rotation by registering a second public key in FileSystemKeyProvider."""
    provider = FileSystemKeyProvider(active_kid="key-v1")
    # Generate second key
    rot_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rot_pub_pem = (
        rot_priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )

    provider.add_rotation_public_key("key-v2-rotation", rot_pub_pem)
    service = JWTService(key_provider=provider)

    jwks = service.get_jwks()
    assert len(jwks["keys"]) == 2
    kids = [k["kid"] for k in jwks["keys"]]
    assert "key-v1" in kids
    assert "key-v2-rotation" in kids


def test_jwks_api_endpoint_response():
    """Test GET /.well-known/jwks.json returns 200 OK with caching headers and keys array."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from auth.router import router as auth_router

    app = FastAPI()
    app.include_router(auth_router)

    client = TestClient(app)
    res = client.get("/.well-known/jwks.json")

    assert res.status_code == 200
    assert "Cache-Control" in res.headers
    assert "ETag" in res.headers

    payload = res.json()
    assert "keys" in payload
    assert isinstance(payload["keys"], list)
    assert len(payload["keys"]) >= 1
    assert payload["keys"][0]["kty"] == "RSA"
    assert payload["keys"][0]["alg"] == "RS256"
