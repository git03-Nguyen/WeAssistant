"""Pydantic schemas for request/response models."""

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import (
    DocumentIngestResponse,
    DocumentListResponse,
    DocumentRemoveResponse,
    DocumentResponse,
)
from app.schemas.message import (
    HistoryMessageResponse,
    HistoryMessagesResponse,
)
from app.schemas.thread import (
    ThreadListResponse,
    ThreadResponse,
    ThreadWithMessagesResponse,
)
from app.schemas.user import (
    UserCreateRequest,
    UserResponse,
)

__all__ = [
    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    # Document schemas
    "DocumentIngestResponse",
    "DocumentRemoveResponse",
    "DocumentListResponse",
    "DocumentResponse",
    # User schemas
    "UserCreateRequest",
    "UserResponse",
    # Thread schemas
    "ThreadResponse",
    "ThreadWithMessagesResponse",
    "ThreadListResponse",
    # Message schemas
    "HistoryMessageResponse",
    "HistoryMessagesResponse",
]
