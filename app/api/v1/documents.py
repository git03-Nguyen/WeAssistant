"""Document management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_rag_service
from app.core.exceptions import WeAssistantException
from app.schemas.document import (
    DocumentIngestResponse,
    DocumentListResponse,
    DocumentRemoveRequest,
    DocumentRemoveResponse,
    DocumentResponse,
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


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    file: UploadFile = File(
        ..., description="Text or Markdown file (.txt/.md) to ingest (max 10MB)"
    ),
    title: str = Form(..., description="Document title"),
    metadata: Optional[str] = Form(None, description="JSON metadata (optional)"),
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentIngestResponse:
    """Ingest a text or markdown file into the RAG system."""
    try:
        document = await doc_service.ingest_document(
            file=file,
            title=title,
            metadata_str=metadata,
        )
        await doc_service.session.commit()

        return DocumentIngestResponse(
            success=True,
            document_id=str(document.id),
            chunks_created=document.chunks_created,
            message="Document successfully ingested",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
