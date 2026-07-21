from datetime import datetime
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base, AuditMixin


class TaskModel(Base, AuditMixin):
    """Database model for persistent tracking of background worker tasks."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
