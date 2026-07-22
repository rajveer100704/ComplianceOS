from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Enum as SQLEnum, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, AuditMixin, generate_uuid
from database.models.enums import MembershipRole

if TYPE_CHECKING:
    from database.models.organization import Organization
    from database.models.user import User


class OrganizationMembership(Base, AuditMixin):
    """Links a User to an Organization with a per-org role assignment."""

    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", name="uq_org_memberships_org_user"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MembershipRole] = mapped_column(
        SQLEnum(
            MembershipRole,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        default=MembershipRole.REVIEWER,
        nullable=False,
    )
    invited_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="memberships"
    )
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="memberships"
    )
    inviter: Mapped["User | None"] = relationship("User", foreign_keys=[invited_by])
