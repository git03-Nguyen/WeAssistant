"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class WeAssistantException(Exception):
    """Base exception for WeAssistant application."""

    def __init__(
        self,
        message: str = "An error occurred",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(WeAssistantException):
    """Raised when there's a database error."""

    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(message, status_code=500, **kwargs)


class ConfigurationError(WeAssistantException):
    """Raised when there's a configuration error."""

    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message, status_code=500, **kwargs)


class RAGServiceError(WeAssistantException):
    """Raised when there's a RAG service error."""

    def __init__(self, message: str = "RAG service error", **kwargs):
        super().__init__(message, status_code=502, **kwargs)
