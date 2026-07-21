from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, AuditMixin, generate_uuid

if TYPE_CHECKING:
    from database.models.user import User
    from database.models.session_model import SessionModel


class RefreshToken(Base, AuditMixin):
    """Hashed refresh token with rotation, family tracking, and replay detection attributes."""

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        CheckConstraint(
            "expires_at > created_at", name="ck_refresh_tokens_expires_after_created"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    token_family: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    rotation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proof_key_thumbprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    replaced_by_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
    session: Mapped["SessionModel | None"] = relationship("SessionModel")
