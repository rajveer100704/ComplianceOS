"""SQLAlchemy ORM models for Policy Storage, Versioning, Packs, Dependencies, and Analytics."""

import enum
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import (
    String,
    Boolean,
    Integer,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base


class PolicyVersionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class PolicyRuleType(str, enum.Enum):
    APPROVAL_GATE = "APPROVAL_GATE"
    RISK_ESCALATION = "RISK_ESCALATION"
    VALIDATION = "VALIDATION"
    WORKFLOW = "WORKFLOW"


class AnalyticsPeriodType(str, enum.Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"


class SystemPolicyPackModel(Base):
    """Global immutable compliance framework template (e.g. FAA Part 450, NRC 10 CFR, SOC2)."""

    __tablename__ = "system_policy_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    framework: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    is_system_pack: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class OrganizationPolicyPackModel(Base):
    """Tenant-installed policy pack instance containing editable policy copies."""

    __tablename__ = "organization_policy_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    system_pack_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("system_policy_packs.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )


class PolicyModel(Base):
    """Policy header entity owned by an organization or policy pack."""

    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    pack_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("organization_policy_packs.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_event: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    current_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Relationships
    versions: Mapped[List["PolicyVersionModel"]] = relationship(
        "PolicyVersionModel", back_populates="policy", cascade="all, delete-orphan"
    )


class PolicyVersionModel(Base):
    """Immutable policy version containing compiled AST expressions and checksums."""

    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    expression: Mapped[str] = mapped_column(Text, nullable=False)
    compiled_expression_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[PolicyVersionStatus] = mapped_column(
        SQLEnum(PolicyVersionStatus), default=PolicyVersionStatus.DRAFT, index=True
    )
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    policy: Mapped["PolicyModel"] = relationship(
        "PolicyModel", back_populates="versions"
    )
    rules: Mapped[List["PolicyRuleModel"]] = relationship(
        "PolicyRuleModel", back_populates="policy_version", cascade="all, delete-orphan"
    )


class PolicyRuleModel(Base):
    """Individual rule within a policy version."""

    __tablename__ = "policy_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policy_versions.id", ondelete="CASCADE"), index=True
    )
    rule_type: Mapped[PolicyRuleType] = mapped_column(
        SQLEnum(PolicyRuleType), nullable=False
    )
    action_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action_config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    policy_version: Mapped["PolicyVersionModel"] = relationship(
        "PolicyVersionModel", back_populates="rules"
    )


class PolicyDependencyModel(Base):
    """Parent-child dependency relationship between policies."""

    __tablename__ = "policy_dependencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    parent_policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="CASCADE"), index=True
    )
    child_policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="CASCADE"), index=True
    )


class PolicyAnalyticsSnapshotModel(Base):
    """Time-series analytics rollup snapshot for a policy."""

    __tablename__ = "policy_analytics_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("policies.id", ondelete="CASCADE"), index=True
    )
    period_type: Mapped[AnalyticsPeriodType] = mapped_column(
        SQLEnum(AnalyticsPeriodType), nullable=False
    )
    period_timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    times_executed: Mapped[int] = mapped_column(Integer, default=0)
    allow_rate: Mapped[float] = mapped_column(Float, default=0.0)
    block_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
