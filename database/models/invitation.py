from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, AuditMixin, generate_uuid
from database.models.enums import MembershipRole, InvitationStatus

if TYPE_CHECKING:
    from database.models.organization import Organization
    from database.models.user import User


class Invitation(Base, AuditMixin):
    """Pending organization invitation with a secure hashed token."""

    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[MembershipRole] = mapped_column(
        SQLEnum(
            MembershipRole,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        default=MembershipRole.REVIEWER,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[InvitationStatus] = mapped_column(
        SQLEnum(
            InvitationStatus,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        default=InvitationStatus.PENDING,
        nullable=False,
        index=True,
    )
    invited_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    inviter: Mapped["User | None"] = relationship("User", foreign_keys=[invited_by])
