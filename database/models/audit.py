from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin


class AuditLogModel(Base, AuditMixin):
    """Maps audit logs recording pipeline run states and Human-in-the-Loop review logs."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    detail: Mapped[str] = mapped_column(nullable=False)

    # Relationships
    request = relationship("RequestModel", back_populates="audit_logs")
