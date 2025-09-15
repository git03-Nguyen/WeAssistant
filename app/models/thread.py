"""Thread domain models."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.message import Message

if TYPE_CHECKING:
    from app.models.user import User


class Thread(BaseModel):
    """Thread domain model for conversation threads."""

    __tablename__ = "threads"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="threads", lazy="select")

    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="thread", cascade="all, delete-orphan", lazy="select"
    )
