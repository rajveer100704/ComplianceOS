"""SQLAlchemy ORM models for Workflow Definitions, Executions, and Step History."""

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


class WorkflowExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStepStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class WorkflowDefinitionModel(Base):
    """Workflow definition storing DAG topology and active status."""

    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    dag_topology_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    executions: Mapped[List["WorkflowExecutionModel"]] = relationship(
        "WorkflowExecutionModel",
        back_populates="workflow_definition",
        cascade="all, delete-orphan",
    )


class WorkflowExecutionModel(Base):
    """Runtime execution record for a Workflow run."""

    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        index=True,
    )
    policy_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(32), default="EVENT")
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[WorkflowExecutionStatus] = mapped_column(
        SQLEnum(WorkflowExecutionStatus),
        default=WorkflowExecutionStatus.PENDING,
        index=True,
    )
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False)

    workflow_definition: Mapped["WorkflowDefinitionModel"] = relationship(
        "WorkflowDefinitionModel", back_populates="executions"
    )
    steps: Mapped[List["WorkflowStepExecutionModel"]] = relationship(
        "WorkflowStepExecutionModel",
        back_populates="execution",
        cascade="all, delete-orphan",
    )


class WorkflowStepExecutionModel(Base):
    """Individual action step execution record with latency and retry logs."""

    __tablename__ = "workflow_step_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), index=True
    )
    action_key: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[WorkflowStepStatus] = mapped_column(
        SQLEnum(WorkflowStepStatus), default=WorkflowStepStatus.PENDING
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    execution: Mapped["WorkflowExecutionModel"] = relationship(
        "WorkflowExecutionModel", back_populates="steps"
    )
