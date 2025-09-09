"""File processing utilities for document ingestion."""

import json
from typing import Optional, Tuple

from fastapi import UploadFile
from langchain.schema import Document
from langchain.text_splitter import (
    MarkdownHeaderTextSplitter,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)


class FileProcessor:
    """Handles file content extraction and validation for .txt and .md files only."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    async def process_file(
        cls, file: UploadFile, title: str, metadata_str: Optional[str] = None
    ) -> Tuple[str, str, dict]:
        """Process uploaded .txt or .md file and extract content."""
        # Validate file extension
        filename = file.filename or ""
        if not filename.lower().endswith((".txt", ".md")):
            raise ValueError("Only .txt and .md files are supported")

        # Validate file size
        content_bytes = await file.read()
        if len(content_bytes) > cls.MAX_FILE_SIZE:
            raise ValueError("File size exceeds 10MB limit")

        # Parse metadata
        metadata = {}
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in metadata field")

        # Add file info to metadata
        metadata.update(
            {
                "original_filename": filename,
                "title": title,
                "size_bytes": len(content_bytes),
            }
        )

        # Extract content as UTF-8 text
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("File must be valid UTF-8 text")

        content_type = (
            "text/markdown" if filename.lower().endswith(".md") else "text/plain"
        )

        return content, content_type, metadata


class SmartSplitter:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 400,
    ):
        self._chunk_size = max(100, chunk_size)
        self._chunk_overlap = min(chunk_size - 50, max(0, chunk_overlap))

        self._markdown_header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("##", "h2")],
            return_each_line=False,
            strip_headers=False,
        )
        self._recursive_character_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!"],
            keep_separator=True,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )

    def _choose_header_splitter(self, content_type: str):
        ctype = content_type.lower()
        if "markdown" in ctype:
            return self._markdown_header_splitter
        # fallback: plain text
        return self._recursive_character_splitter

    # The main method to split text into chunks
    def split_text(
        self,
        content: str,
        content_type: str = "text/markdown",
    ) -> list[Document]:
        """Pipeline entry - returns list[Document] ready for embeddings."""

        header_splitter = self._choose_header_splitter(content_type)
        docs: list[Document] = []
        for section in header_splitter.split_text(content):
            if isinstance(section, Document):
                docs.append(section)
            elif isinstance(section, str):
                docs += [Document(page_content=section)]
        return docs
