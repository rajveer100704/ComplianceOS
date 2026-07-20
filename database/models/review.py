from sqlalchemy import String, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin

class ReviewAssignmentModel(Base, AuditMixin):
    """Tracks reviewer assignments history for request audits."""
    __tablename__ = "review_assignments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_by: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_at: Mapped[str] = mapped_column(String(100), nullable=False)
    unassigned_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ReviewActivityLogModel(Base, AuditMixin):
    """Immutable audit trail for review timeline events."""
    __tablename__ = "review_activity_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    user: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(nullable=False)


class CommentMentionModel(Base, AuditMixin):
    """Tracks explicit reviewer tags inside claim comments."""
    __tablename__ = "comment_mentions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("claim_comments.id"), nullable=False)
    user: Mapped[str] = mapped_column(String(100), nullable=False)


class ClaimCommentModel(Base, AuditMixin):
    """Threaded claim discussions with self-referential parent/nested replies."""
    __tablename__ = "claim_comments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("claim_comments.id"), nullable=True)
    user: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)

    # Relationships
    claim = relationship("ClaimModel", back_populates="comments_list", lazy="raise")


class PinnedEvidenceModel(Base, AuditMixin):
    """Reviewer pinned chunks serving as supporting/contradicting evidence for claims."""
    __tablename__ = "pinned_evidences"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(100), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="PRIMARY", nullable=False)  # PRIMARY, SUPPORTING, CONTRADICTING
    pinned_by: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    claim = relationship("ClaimModel", back_populates="pinned_evidences_list", lazy="raise")
    document = relationship("DocumentModel", lazy="raise")


class ReviewSnapshotModel(Base, AuditMixin):
    """Audit snapshot capturing review state at a point in time."""
    __tablename__ = "review_snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    creator: Mapped[str] = mapped_column(String(100), nullable=False)
    request_status: Mapped[str] = mapped_column(String(50), nullable=False)
    config_hash: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
