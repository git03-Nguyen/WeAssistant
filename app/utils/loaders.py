"""File processing utilities for document ingestion."""

from typing import Tuple

from fastapi import UploadFile

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def aload_md_file(
    file: UploadFile,
    title: str,
    custom_metadata: dict,
) -> Tuple[str, dict]:
    """Process uploaded .md file and extract content."""

    # Validate file extension
    filename = file.filename or ""
    if not filename.lower().endswith(".md"):
        raise ValueError("Only .md files are supported")

    # Validate file size
    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 10MB limit")

    # Parse metadata
    metadata = {
        "original_filename": filename,
        "title": title,
        "size_bytes": len(content_bytes),
        **custom_metadata,
    }

    # Extract content as UTF-8 text
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("File must be valid UTF-8 text")

    return content, metadata
