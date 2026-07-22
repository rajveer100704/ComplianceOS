from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, AuditMixin, generate_uuid
from database.models.enums import OrganizationPlan

if TYPE_CHECKING:
    from database.models.membership import OrganizationMembership
    from database.models.team import Team


class Organization(Base, AuditMixin):
    """Tenant root entity — every compliance resource belongs to one organization."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    plan: Mapped[OrganizationPlan] = mapped_column(
        SQLEnum(
            OrganizationPlan,
            native_enum=False,
            values_callable=lambda e: [i.value for i in e],
        ),
        default=OrganizationPlan.FREE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    memberships: Mapped[List["OrganizationMembership"]] = relationship(
        "OrganizationMembership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
