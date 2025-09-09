"""File processing utilities for document ingestion."""

import json
from typing import Optional, Tuple

import spacy
from fastapi import UploadFile
from langchain.schema import Document
from langchain.text_splitter import (
    MarkdownHeaderTextSplitter,
    SpacyTextSplitter,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
    """Two-stage splitter: (1) structure-aware -> (2) spaCy sentence-aware."""

    _MODEL_BY_LANG: dict[str, str] = {
        "en": "en_core_web_sm",
        "vi": "vi_core_news_sm",
        # add more if you pre-download them
    }

    # preload default model
    spacy.load("en_core_web_sm")
    # ──────────────────────────────────────────────────────────────────────────

    def __init__(
        self,
        lang: str = "en",
        chunk_size: int = 800,
        chunk_overlap: int = 400,
    ):
        # sentence splitter (stage-2) - always spaCy
        pipeline = self._MODEL_BY_LANG.get(lang.lower(), "sentencizer")
        self._sentence_splitter = SpacyTextSplitter(
            pipeline=pipeline,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    # ──────────────────────────────────────────────────────────────────────────
    def _choose_header_splitter(self, content_type: str):
        ctype = content_type.lower()
        if "markdown" in ctype:
            return MarkdownHeaderTextSplitter(
                headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
                return_each_line=False,
                strip_headers=True,
                custom_header_patterns=None,
            )
        # fallback: plain text
        return RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            is_separator_regex=False,
            keep_separators=False,
            strip_white_space=True,
            chunk_size=self._sentence_splitter._chunk_size,
            chunk_overlap=self._sentence_splitter._chunk_overlap,
        )

    # ──────────────────────────────────────────────────────────────────────────
    def split_text(
        self,
        content: str,
        content_type: str = "text/plain",
        lang: str | None = None,
    ) -> list[Document]:
        """Pipeline entry - returns list[Document] ready for embeddings."""
        if lang:  # allow per-call override
            self.__init__(lang)

        header_splitter = self._choose_header_splitter(content_type)
        docs: list[Document] = []
        for section in header_splitter.split_text(content):
            if isinstance(section, Document):
                final_docs = self._sentence_splitter.split_documents([section])
            elif isinstance(section, str):
                content_doc = self._sentence_splitter.split_text(section)
                final_docs = [Document(page_content=txt) for txt in content_doc]
            docs += final_docs
        return docs
