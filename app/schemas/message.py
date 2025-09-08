"""Message-related Pydantic schemas."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MessageCreateRequest(BaseModel):
    """Request schema for creating a new message."""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., min_length=1, description="The actual message content")
    thread_id: str = Field(..., description="Thread ID where the message belongs")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, can you help me with trading?",
                "thread_id": "thread-123e4567-e89b-12d3-a456-426614174000",
            }
        }


class MessageUpdateRequest(BaseModel):
    """Request schema for updating a message."""

    content: Optional[str] = Field(
        None, min_length=1, description="The actual message content"
    )

    class Config:
        json_schema_extra = {
            "example": {"content": "Hello, can you help me with investment strategies?"}
        }


class MessageResponse(BaseModel):
    """Message response schema."""

    id: str = Field(..., description="Message ID")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Role of the message sender"
    )
    content: str = Field(..., description="The actual message content")
    thread_id: str = Field(..., description="Thread ID where the message belongs")
    created_at: datetime = Field(..., description="Message creation date")
    updated_at: datetime = Field(..., description="Last update date")
    deleted_at: Optional[datetime] = Field(
        None, description="Deletion date if soft deleted"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "msg-123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "Hello, can you help me?",
                "thread_id": "thread-123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "deleted_at": None,
            }
        }


class MessageListResponse(BaseModel):
    """Response schema for message list."""

    messages: list[MessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": "msg-123e4567-e89b-12d3-a456-426614174000",
                        "role": "user",
                        "content": "Hello, can you help me?",
                        "thread_id": "thread-123e4567-e89b-12d3-a456-426614174000",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "deleted_at": None,
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10,
            }
        }
