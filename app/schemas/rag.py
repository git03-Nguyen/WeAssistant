"""RAG-related Pydantic schemas."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentIngestRequest(BaseModel):
    """Request schema for document ingestion."""

    content: str = Field(..., min_length=1, description="Text content to ingest")
    metadata: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Optional metadata for the document"
    )
    chunk_size: Optional[int] = Field(
        default=1000, ge=100, le=4000, description="Size of text chunks"
    )
    chunk_overlap: Optional[int] = Field(
        default=200, ge=0, le=1000, description="Overlap between chunks"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is a sample document content that will be ingested into the RAG system.",
                "metadata": {"source": "manual_upload", "category": "trading_guide"},
                "chunk_size": 1000,
                "chunk_overlap": 200,
            }
        }


class DocumentIngestResponse(BaseModel):
    """Response schema for document ingestion."""

    success: bool = Field(..., description="Whether the ingestion was successful")
    document_id: str = Field(
        ..., description="Unique identifier for the ingested document"
    )
    chunks_created: int = Field(
        ..., description="Number of chunks created from the document"
    )
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "document_id": "doc_123456",
                "chunks_created": 5,
                "message": "Document successfully ingested",
            }
        }


class DocumentRemoveRequest(BaseModel):
    """Request schema for document removal."""

    document_id: Optional[str] = Field(
        default=None, description="Specific document ID to remove"
    )
    metadata_filter: Optional[Dict[str, str]] = Field(
        default=None, description="Remove documents matching metadata filter"
    )

    class Config:
        json_schema_extra = {"example": {"document_id": "doc_123456"}}

    def model_post_init(self, __context) -> None:
        """Validate that either document_id or metadata_filter is provided."""
        if not self.document_id and not self.metadata_filter:
            raise ValueError("Either document_id or metadata_filter must be provided")


class DocumentRemoveResponse(BaseModel):
    """Response schema for document removal."""

    success: bool = Field(..., description="Whether the removal was successful")
    documents_removed: int = Field(..., description="Number of documents removed")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "documents_removed": 1,
                "message": "Document successfully removed",
            }
        }


class DocumentSearchRequest(BaseModel):
    """Request schema for document search."""

    query: str = Field(..., min_length=1, description="Search query")
    k: Optional[int] = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )
    metadata_filter: Optional[Dict[str, str]] = Field(
        default=None, description="Filter documents by metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "trading strategies",
                "k": 5,
                "metadata_filter": {"category": "trading_guide"},
            }
        }


class DocumentSearchResult(BaseModel):
    """Single document search result."""

    content: str = Field(..., description="Document content")
    metadata: Dict[str, str] = Field(..., description="Document metadata")
    score: float = Field(..., description="Similarity score")


class DocumentSearchResponse(BaseModel):
    """Response schema for document search."""

    results: List[DocumentSearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results found")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "content": "Trading strategies involve...",
                        "metadata": {
                            "source": "manual_upload",
                            "category": "trading_guide",
                        },
                        "score": 0.95,
                    }
                ],
                "total_results": 1,
            }
        }
