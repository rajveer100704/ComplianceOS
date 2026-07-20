from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin

class RequestModel(Base, AuditMixin):
    """Maps request records including project regulator settings and lifecycle states."""
    __tablename__ = "requests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project: Mapped[str] = mapped_column(String(255), nullable=False)
    regulator: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Draft", nullable=False)
    owner: Mapped[str] = mapped_column(String(100), nullable=False)
    approved_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_reviewer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    documents = relationship("DocumentModel", back_populates="request", cascade="all, delete-orphan")
    runs = relationship("RunModel", back_populates="request", cascade="all, delete-orphan")
    claims = relationship("ClaimModel", back_populates="request", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogModel", back_populates="request", cascade="all, delete-orphan")
