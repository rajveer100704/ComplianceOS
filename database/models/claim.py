from sqlalchemy import String, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin


class ClaimModel(Base, AuditMixin):
    """Maps extracted document sentences marked for compliance review."""

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    text: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    citation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    citation_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snippet: Mapped[str | None] = mapped_column(nullable=True)
    reason: Mapped[str | None] = mapped_column(nullable=True)
    reviewer_decision: Mapped[str] = mapped_column(
        String(50), default="Needs Review", nullable=False
    )
    comment: Mapped[str | None] = mapped_column(nullable=True)
    resolved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_notes: Mapped[str | None] = mapped_column(nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    request = relationship("RequestModel", back_populates="claims")
    run = relationship("RunModel", back_populates="claims")
    document = relationship("DocumentModel", back_populates="claims")
    comments_list = relationship(
        "ClaimCommentModel", back_populates="claim", cascade="all, delete-orphan"
    )
    pinned_evidences_list = relationship(
        "PinnedEvidenceModel", back_populates="claim", cascade="all, delete-orphan"
    )
