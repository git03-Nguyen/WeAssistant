"""Document schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    """Request to upload a new document."""

    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)


class DocumentIngestRequest(BaseModel):
    """Request to ingest an uploaded document."""

    document_id: str = Field(..., description="Document ID to ingest")


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: str
    filename: str
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


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    success: bool
    document_id: str
    message: str


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
