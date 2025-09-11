"""Document service for managing uploaded files and their processing."""

from typing import List

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ingestor import aadd_documents, adelete_embedded_chunks
from app.models.document import Document, DocumentStatus
from app.utils.loaders import aload_md_file


class DocumentService:
    """Service for managing documents and their processing status."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def aingest_document(
        self,
        file: UploadFile,
        title: str,
        custom_metadata: dict = {},
    ) -> Document:
        """Create and ingest a document from uploaded file."""

        content, metadata = await aload_md_file(file, title, custom_metadata)
        document = Document(
            filename=file.filename or "unknown",
            title=title,
            content_type=metadata.get("content_type", ""),
            size_bytes=metadata.get("size_bytes", 0),
            doc_metadata=metadata,
            chunk_ids=[],
            status=DocumentStatus.INGESTING,
        )

        self.session.add(document)
        await self.session.flush()
        document_id = str(document.id)

        metadata = {
            "document_id": document_id,
            **metadata,
        }

        try:
            chunk_ids = await aadd_documents(content, metadata)
            document.chunk_ids = chunk_ids
            document.status = DocumentStatus.COMPLETED
            await self.session.commit()
            await self.session.refresh(document)
            return document
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await self.session.commit()
            await self.session.refresh(document)
            return document

    async def aget_all_documents(self) -> List[Document]:
        """Get all documents."""
        stmt = (
            select(Document)
            .where(Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def aremove_document(self, document_id: str) -> bool:
        """Hard delete document and its vector data."""
        document = await self.session.get(Document, document_id)
        if not document:
            return False

        await adelete_embedded_chunks(document.chunk_ids or [])
        await self.session.delete(document)
        await self.session.commit()
        return True