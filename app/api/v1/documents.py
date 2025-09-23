"""Document management endpoints."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_document_service
from app.schemas.document import (
    DocumentIngestResponse,
    DocumentListIngestResponse,
    DocumentListResponse,
    DocumentRemoveResponse,
    DocumentResponse,
)
from app.services.documents import DocumentService

router = APIRouter()


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    file: UploadFile = File(
        ..., description="Markdown file (.md) to ingest (max 10MB)"
    ),
    metadata: Optional[str] = Form(None, description="JSON metadata (optional)"),
    *,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentIngestResponse:
    """Ingest a markdown file into the RAG system."""
    try:
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
                if not isinstance(metadata_dict, dict):
                    raise ValueError("Metadata must be a JSON object")
            except json.JSONDecodeError:
                raise ValueError("Metadata must be valid JSON")

        document = await doc_service.aingest_document(
            file=file,
            title=file.filename or "Untitled",
            custom_metadata=metadata_dict,
        )

        return DocumentIngestResponse(
            success=True,
            document_id=str(document.id),
            chunk_ids=document.chunk_ids,
            message="Document successfully ingested",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/bulk-ingest", response_model=DocumentListIngestResponse)
async def ingest_bulk_documents(
    files: list[UploadFile] = File(
        ..., description="Markdown files (.md) to ingest (each max 10MB)"
    ),
    metadata: Optional[str] = Form(None, description="JSON metadata (optional)"),
    *,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentListIngestResponse:
    """Ingest a markdown file into the RAG system."""
    results = []

    try:
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
                if not isinstance(metadata_dict, dict):
                    raise ValueError("Metadata must be a JSON object")
            except json.JSONDecodeError:
                raise ValueError("Metadata must be valid JSON")

        for file in files:
            try:
                document = await doc_service.aingest_document(
                    file=file,
                    title=file.filename or "Untitled",
                    custom_metadata=metadata_dict,
                )
                results.append(
                    DocumentIngestResponse(
                        success=True,
                        document_id=str(document.id),
                        chunk_ids=document.chunk_ids,
                        message="Document successfully ingested",
                    )
                )
                print(f"Ingested document ID: {document.id}")
            except Exception as e:
                results.append(
                    DocumentIngestResponse(
                        success=False,
                        document_id="",
                        chunk_ids=None,
                        message=f"Failed to ingest {file.filename}: {str(e)}",
                    )
                )
                print(f"Failed to ingest document ID: {document.id}")
        return DocumentListIngestResponse(results=results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def get_all_uploads(
    *,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """Get all uploaded documents."""
    try:
        documents = await doc_service.aget_all_documents()
        return DocumentListResponse(
            documents=[DocumentResponse.model_validate(doc) for doc in documents],
            total=len(documents),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/remove/{document_id}", response_model=DocumentRemoveResponse)
async def remove_document(
    document_id: str,
    *,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentRemoveResponse:
    """Remove a document from the system."""
    try:
        if await doc_service.aremove_document(document_id):
            return DocumentRemoveResponse(
                success=True,
                message="Document successfully removed",
            )
        else:
            return DocumentRemoveResponse(
                success=False,
                message="Document not found",
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
