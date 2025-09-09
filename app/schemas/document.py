"""Document schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentIngestForm(BaseModel):
    """Form data for document ingestion."""

    title: str = Field(..., min_length=1, max_length=255)
    metadata: Optional[str] = Field(None, description="JSON string of metadata")


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: str
    filename: str
    title: str
    content_type: Optional[str]
    size_bytes: Optional[int]
    status: str
    chunks_created: int
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
    chunks_created: Optional[int] = None
    message: str


class DocumentRemoveRequest(BaseModel):
    """Request to remove a document."""

    document_id: str = Field(..., description="Document ID to remove")


class DocumentRemoveResponse(BaseModel):
    """Response after removing a document."""

    success: bool
    message: str
