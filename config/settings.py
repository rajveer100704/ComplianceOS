from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # General Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Execution environment (development, staging, production)",
    )
    DEBUG: bool = Field(default=True, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Log verbosity level")

    # Security & Auth Settings
    AUTH_SECRET: str = Field(
        default="complianceos-default-development-secret-key-32bytes",
        description="Secret key for auth token signing",
    )
    API_KEY: str = Field(
        default="dev-compliance-api-key-2026",
        description="API key for static authorization",
    )
    AUTH_PROVIDER: str = Field(
        default="api_key",
        description="Active authentication provider ('api_key' or 'jwt')",
    )
    AUTH_JWT_ALGORITHM: str = Field(default="RS256", description="JWT algorithm")
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, description="Access token TTL in minutes"
    )
    AUTH_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token TTL in days"
    )
    AUTH_REFRESH_REPLAY_GRACE_SECONDS: int = Field(
        default=10, description="Replay revocation grace window in seconds"
    )
    AUTH_SESSION_TOUCH_INTERVAL_SECONDS: int = Field(
        default=60,
        description="Throttled session activity heartbeat interval in seconds",
    )
    AUTH_SESSION_IDLE_EXPIRE_DAYS: int = Field(
        default=30, description="Session idle inactivity timeout in days"
    )
    AUTH_SESSION_ABSOLUTE_EXPIRE_DAYS: int = Field(
        default=90, description="Session absolute hard expiration timeout in days"
    )
    AUTH_KEY_ID: str = Field(
        default="complianceos-key-v1", description="Active RSA key ID"
    )
    AUTH_RSA_PRIVATE_KEY: str | None = Field(
        default=None, description="PEM string for RS256 private key override"
    )
    AUTH_RSA_PUBLIC_KEY: str | None = Field(
        default=None, description="PEM string for RS256 public key override"
    )
    CORS_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=120, description="Max requests per minute per client IP"
    )

    # Database & Storage
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./compliance.db",
        description="SQLAlchemy database URL",
    )
    QDRANT_URL: str = Field(
        default="http://localhost:6333", description="Qdrant vector database URL"
    )
    QDRANT_COLLECTION: str = Field(
        default="compliance_regulations", description="Vector collection name"
    )

    # Worker Settings
    WORKER_POLL_INTERVAL_SEC: float = Field(
        default=2.0, description="Worker queue polling interval in seconds"
    )

    # Observability & Monitoring Settings
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = Field(
        default=None, description="OpenTelemetry OTLP exporter gRPC/HTTP endpoint"
    )
    OTEL_SERVICE_NAME: str = Field(
        default="complianceos-api", description="OpenTelemetry service name tag"
    )
    TRACING_ENABLED: bool = Field(
        default=True, description="Enable OpenTelemetry distributed tracing"
    )
    PROMETHEUS_METRICS_ENABLED: bool = Field(
        default=True, description="Enable Prometheus metrics exposition"
    )
    SENTRY_DSN: str | None = Field(
        default=None, description="Sentry DSN for exception tracking"
    )

    def validate_startup(self) -> List[str]:
        """Perform fail-fast startup checks. Returns list of warning or error messages."""
        issues = []
        if self.ENVIRONMENT == "production":
            if (
                self.AUTH_SECRET
                == "complianceos-default-development-secret-key-32bytes"
            ):
                issues.append(
                    "CRITICAL: Production environment is using default AUTH_SECRET."
                )
            if self.API_KEY == "dev-compliance-api-key-2026":
                issues.append(
                    "CRITICAL: Production environment is using default API_KEY."
                )
            if "*" in self.CORS_ORIGINS:
                issues.append("WARNING: Wildcard CORS origin is enabled in production.")
        return issues


settings = Settings()
