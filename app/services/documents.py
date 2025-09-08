"""Document service for managing uploaded files and their processing."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.document import Document, DocumentStatus
from app.services.rag import RAGService


class DocumentService:
    """Service for managing documents and their processing status."""

    def __init__(self, session: AsyncSession, rag_service: Optional[RAGService] = None):
        self.session = session
        self.rag_service = rag_service

    async def create_document(
        self,
        filename: str,
        content: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Document:
        """Create a new document record."""
        try:
            document = Document(
                filename=filename,
                content=content,
                content_type=content_type,
                size_bytes=len(content.encode("utf-8")),
                doc_metadata=metadata or {},
                status=DocumentStatus.NONE,
            )

            self.session.add(document)
            await self.session.flush()
            return document

        except Exception as e:
            raise DatabaseError(f"Failed to create document: {e}")

    async def get_all_documents(self) -> List[Document]:
        """Get all documents."""
        try:
            stmt = (
                select(Document)
                .where(Document.deleted_at.is_(None))
                .order_by(Document.created_at.desc())
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            raise DatabaseError(f"Failed to get documents: {e}")

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        try:
            return await self.session.get(Document, document_id)
        except Exception as e:
            raise DatabaseError(f"Failed to get document: {e}")

    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        chunks_created: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update document status."""
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}

            if status == DocumentStatus.COMPLETED:
                update_data["ingested_at"] = datetime.utcnow()
                if chunks_created is not None:
                    update_data["chunks_created"] = chunks_created

            elif status == DocumentStatus.FAILED and error_message:
                update_data["error_message"] = error_message

            stmt = (
                update(Document).where(Document.id == document_id).values(**update_data)
            )

            result = await self.session.execute(stmt)
            return result.rowcount > 0

        except Exception as e:
            raise DatabaseError(f"Failed to update document status: {e}")

    async def ingest_document(self, document_id: str) -> bool:
        """Process document ingestion with RAG service."""
        if not self.rag_service:
            raise ValueError("RAG service not available")

        try:
            # Get document
            document = await self.get_document(document_id)
            if not document:
                return False

            # Update status to ingesting
            await self.update_document_status(document_id, DocumentStatus.INGESTING)
            await self.session.commit()

            try:
                # Ingest with RAG service
                content = document.content or ""
                metadata = document.doc_metadata or {}

                await self.rag_service.ingest_document(content, metadata)

                # Calculate chunks (rough estimate)
                chunks_created = len(content) // 800 + 1

                # Update status to completed
                await self.update_document_status(
                    document_id, DocumentStatus.COMPLETED, chunks_created=chunks_created
                )
                await self.session.commit()
                return True

            except Exception as e:
                # Update status to failed
                await self.update_document_status(
                    document_id, DocumentStatus.FAILED, error_message=str(e)
                )
                await self.session.commit()
                return False

        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to ingest document: {e}")

    async def remove_document(self, document_id: str) -> bool:
        """Remove document and its vector data."""
        try:
            document = await self.get_document(document_id)
            if not document:
                return False

            # Try to remove from RAG service if available
            if self.rag_service:
                try:
                    await self.rag_service.remove_document(document_id)
                except Exception as e:
                    print(f"Warning: Failed to remove document from RAG: {e}")

            # Soft delete the document
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(deleted_at=datetime.utcnow())
            )

            result = await self.session.execute(stmt)
            return result.rowcount > 0

        except Exception as e:
            raise DatabaseError(f"Failed to remove document: {e}")
