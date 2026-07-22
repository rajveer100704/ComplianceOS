import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.models.base import Base
from database.models.enums import (
    IntegrationProvider,
    IntegrationHealthStatus,
    DeliveryStatus,
)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationModel(Base):
    """Represents an organization's third-party integration configuration."""

    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "provider",
            "name",
            name="uq_integrations_org_provider_name",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider = Column(
        SQLEnum(
            IntegrationProvider,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)

    # Encrypted Credentials (AES-256 Fernet)
    encrypted_secret = Column(Text, nullable=True)
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    credential_version = Column(Integer, nullable=False, default=1)
    rotated_at = Column(DateTime(timezone=True), nullable=True)
    rotated_by = Column(String(36), nullable=True)

    metadata_json = Column(Text, nullable=True)  # Stores non-secret config JSON
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # Relationships
    organization = relationship("Organization", back_populates="integrations")
    runtime_state = relationship(
        "IntegrationRuntimeStateModel",
        back_populates="integration",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )
    delivery_logs = relationship(
        "IntegrationDeliveryLogModel",
        back_populates="integration",
        cascade="all, delete-orphan",
    )


class IntegrationRuntimeStateModel(Base):
    """Operational health metrics and probe history for an integration."""

    __tablename__ = "integration_runtime_states"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    integration_id = Column(
        String(36),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    health_status = Column(
        SQLEnum(
            IntegrationHealthStatus,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=IntegrationHealthStatus.HEALTHY,
        index=True,
    )
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    last_error_message = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_probe_duration_ms = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # Relationship
    integration = relationship("IntegrationModel", back_populates="runtime_state")


class IntegrationDeliveryLogModel(Base):
    """Idempotent audit log of event delivery attempts to external integration providers."""

    __tablename__ = "integration_delivery_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    integration_id = Column(
        String(36),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(100), nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=False, unique=True, index=True)
    status = Column(
        SQLEnum(
            DeliveryStatus,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=DeliveryStatus.PENDING,
        index=True,
    )
    attempt_count = Column(Integer, nullable=False, default=1)
    response_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationship
    integration = relationship("IntegrationModel", back_populates="delivery_logs")
