"""Document schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: str
    filename: str
    title: str
    content_type: Optional[str]
    size_bytes: Optional[int]
    status: str
    chunk_ids: list[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    ingested_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: List[DocumentResponse]
    total: int


class DocumentIngestResponse(BaseModel):
    """Response after ingesting a document."""

    success: bool
    document_id: str
    chunk_ids: Optional[list[str]] = None
    message: str


class DocumentRemoveResponse(BaseModel):
    """Response after removing a document."""

    success: bool
    message: str
