"""Thread domain models."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.thread import Thread


class Message(BaseModel):
    """Message domain model for conversation messages."""

    __tablename__ = "messages"

    type: Mapped[str] = mapped_column(nullable=False, index=True)
    content: Mapped[str] = mapped_column(nullable=False)
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    thread_id: Mapped[str] = mapped_column(
        ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True
    )

    thread: Mapped["Thread"] = relationship(
        "Thread", back_populates="messages", lazy="select"
    )
