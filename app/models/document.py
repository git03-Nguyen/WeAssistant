"""Document model for managing uploaded files and their status."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class DocumentStatus(str, Enum):
    """Document processing status."""

    NONE = "NONE"
    INGESTING = "INGESTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(BaseModel):
    """Document model for tracking uploaded files and their processing status."""

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=DocumentStatus.NONE, nullable=False
    )
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    chunks_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional timestamps beyond BaseModel
    ingested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=False), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, title={self.title}, status={self.status})>"
