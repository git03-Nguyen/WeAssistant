"""Pydantic schemas for request/response models."""

from app.schemas.chat import ChatRequest, ChatResponse
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
from app.schemas.message import (
    BaseMessageResponse,
    MessageListResponse,
)
from app.schemas.thread import (
    ThreadCreateRequest,
    ThreadListResponse,
    ThreadResponse,
    ThreadWithMessagesResponse,
)
from app.schemas.user import (
    UserCreateRequest,
    UserProfileClassification,
    UserResponse,
)

__all__ = [
    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    # Document schemas
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    "DocumentIngestRequest",
    "DocumentIngestResponse",
    "DocumentRemoveRequest",
    "DocumentRemoveResponse",
    "DocumentListResponse",
    "DocumentResponse",
    # User schemas
    "UserCreateRequest",
    "UserResponse",
    "UserProfileClassification",
    # Thread schemas
    "ThreadCreateRequest",
    "ThreadResponse",
    "ThreadWithMessagesResponse",
    "ThreadListResponse",
    # Message schemas
    "BaseMessageResponse",
    "MessageListResponse",
]
