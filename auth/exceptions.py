class AuthError(Exception):
    """Base exception for all authentication and authorization domain errors."""

    pass


class InvalidTokenError(AuthError):
    """Raised when a JWT token is invalid or malformed."""

    pass


class TokenExpiredError(InvalidTokenError):
    """Raised when a JWT token exp claim is past expiration time."""

    pass


class TokenNotYetValidError(InvalidTokenError):
    """Raised when a JWT token nbf claim is in the future."""

    pass


class TokenReplayError(InvalidTokenError):
    """Raised when a previously rotated/revoked refresh token is re-used (replay attack)."""

    pass


class InvalidIssuerError(InvalidTokenError):
    """Raised when JWT iss claim does not match expected issuer."""

    pass


class InvalidAudienceError(InvalidTokenError):
    """Raised when JWT aud claim does not match expected audience."""

    pass


class InvalidSignatureError(InvalidTokenError):
    """Raised when JWT signature verification fails."""

    pass


class UnsupportedAlgorithmError(InvalidTokenError):
    """Raised when JWT algorithm is not allowed (e.g., non-RS256)."""

    pass


class MissingClaimError(InvalidTokenError):
    """Raised when a required claim (sub, iss, aud, iat, exp, jti, nbf) is missing."""

    pass


class UnknownKeyIdError(InvalidTokenError):
    """Raised when JWT kid header does not match any known public key."""

    pass
