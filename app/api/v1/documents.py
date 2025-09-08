"""Document management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_rag_service
from app.core.exceptions import WeAssistantException
from app.schemas.document import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentListResponse,
    DocumentRemoveRequest,
    DocumentRemoveResponse,
    DocumentResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.services.documents import DocumentService
from app.services.rag import RAGService
from app.utils.database import get_db

router = APIRouter()


def get_document_service(
    session: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
) -> DocumentService:
    """Get document service instance."""
    return DocumentService(session, rag_service)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: DocumentUploadRequest,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """Upload a new document."""
    try:
        document = await doc_service.create_document(
            filename=request.filename,
            content=request.content,
            content_type=request.content_type,
            metadata=request.metadata,
        )
        await doc_service.session.commit()

        return DocumentUploadResponse(
            success=True,
            document_id=str(document.id),
            message="Document uploaded successfully",
        )
    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    request: DocumentIngestRequest,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentIngestResponse:
    """Ingest an uploaded document into the RAG system."""
    try:
        success = await doc_service.ingest_document(request.document_id)

        if success:
            # Get updated document info
            document = await doc_service.get_document(request.document_id)
            chunks_created = getattr(document, "chunks_created", 0) if document else 0

            return DocumentIngestResponse(
                success=True,
                document_id=request.document_id,
                chunks_created=chunks_created,
                message="Document successfully ingested",
            )
        else:
            return DocumentIngestResponse(
                success=False,
                document_id=request.document_id,
                message="Failed to ingest document",
            )

    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def get_all_uploads(
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """Get all uploaded documents."""
    try:
        documents = await doc_service.get_all_documents()

        return DocumentListResponse(
            documents=[DocumentResponse.model_validate(doc) for doc in documents],
            total=len(documents),
        )

    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/remove", response_model=DocumentRemoveResponse)
async def remove_document(
    request: DocumentRemoveRequest,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentRemoveResponse:
    """Remove a document from the system."""
    try:
        success = await doc_service.remove_document(request.document_id)
        await doc_service.session.commit()

        if success:
            return DocumentRemoveResponse(
                success=True,
                message="Document successfully removed",
            )
        else:
            return DocumentRemoveResponse(
                success=False,
                message="Document not found",
            )

    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
