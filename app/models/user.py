"""User domain models."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.thread import Thread


class User(BaseModel):
    """User domain model."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    withdrawed_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    threads: Mapped[List["Thread"]] = relationship(
        "Thread", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
