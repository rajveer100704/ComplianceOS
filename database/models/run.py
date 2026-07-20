from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin

class RunModel(Base, AuditMixin):
    """Maps execution versions and receipts logs of pipeline evaluations."""
    __tablename__ = "runs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str | None] = mapped_column(nullable=True)
    receipt: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    request = relationship("RequestModel", back_populates="runs")
    claims = relationship("ClaimModel", back_populates="run", cascade="all, delete-orphan")
