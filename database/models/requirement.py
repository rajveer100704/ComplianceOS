from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base


class RequirementModel(Base):
    """Maps seeded regulation requirement corpus data."""

    __tablename__ = "requirements"

    reg_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
