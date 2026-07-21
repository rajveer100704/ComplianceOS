from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin


class DocumentModel(Base, AuditMixin):
    """Maps request uploaded document text and PDF source files."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)

    # Relationships
    request = relationship("RequestModel", back_populates="documents")
    claims = relationship(
        "ClaimModel", back_populates="document", cascade="all, delete-orphan"
    )
