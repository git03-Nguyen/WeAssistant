"""Message domain models."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.thread import Thread


class Message(BaseModel):
    """Message domain model for chat messages."""

    __tablename__ = "messages"

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Role of the message sender (user, assistant, system)",
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="The actual message content"
    )

    # Foreign key with proper constraint
    thread_id: Mapped[str] = mapped_column(
        ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    thread: Mapped["Thread"] = relationship(
        "Thread", back_populates="messages", lazy="select"
    )
