from typing import Any

from langchain.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config.settings import SETTINGS
from app.core.vector_store import aget_vector_store


async def aadd_documents(
    content: str,
    metadata: dict[str, Any],
) -> list[str]:
    """Document ingestion"""
    docs = _split_text(content)
    title = metadata.get("title", "").strip()
    chunk_count = len(docs)
    documents = []
    for i, doc in enumerate(docs):
        doc.page_content = (
            f"[Title: {title} - Part {i + 1} of {chunk_count}]\n{doc.page_content}"
            if chunk_count > 1
            else f"[Title: {title}]\n{doc.page_content}"
        )
        doc.metadata = {
            "chunk_index": i,
            "chunk_length": len(doc.page_content),
            **metadata,
            **doc.metadata,
        }
        documents.append(doc)

    vector_store = await aget_vector_store()
    chunk_ids = await vector_store.aadd_documents(documents)
    return chunk_ids


async def adelete_embedded_chunks(chunk_ids: list[str]) -> bool | None:
    """Remove document chunks from the vector store by their IDs."""
    vector_store = await aget_vector_store()
    return await vector_store.adelete(chunk_ids)


#############################################################################
#############################################################################
############################ Internal Helpers ###############################
#############################################################################
#############################################################################

_markdown_header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "Heading 1"), ("##", "Heading 2")],
    strip_headers=False,
)

_recursive_character_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", "!"],
    keep_separator=True,
    chunk_size=SETTINGS.rag_chunk_size,
    chunk_overlap=SETTINGS.rag_chunk_overlap,
)


def _split_text(text: str) -> list[Document]:
    """Split text into chunks using markdown header and recursive character splitters."""
    chunks = []
    for headers in _markdown_header_splitter.split_text(text):
        for text in _recursive_character_splitter.split_text(headers.page_content):
            chunks.append(
                Document(
                    page_content=text,
                    metadata=headers.metadata,
                )
            )
    return chunks
