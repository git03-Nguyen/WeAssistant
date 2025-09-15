"""Thread-related Pydantic schemas."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.core.state import CustomUsageMetadata


class ThreadResponse(BaseModel):
    """Thread response schema."""

    id: str = Field(..., description="Thread ID")
    user_id: str = Field(..., description="User ID who owns the thread")
    created_at: datetime = Field(..., description="Thread creation date")
    updated_at: datetime = Field(..., description="Last update date")
    deleted_at: Optional[datetime] = Field(
        None, description="Deletion date if soft deleted"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "thread-123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "deleted_at": None,
            }
        }


class ThreadWithMessagesResponse(BaseModel):
    """Thread response schema with messages included."""

    id: str = Field(..., description="Thread ID")
    user_id: str = Field(..., description="User ID who owns the thread")
    created_at: datetime = Field(..., description="Thread creation date")
    updated_at: datetime = Field(..., description="Last update date")
    deleted_at: Optional[datetime] = Field(
        None, description="Deletion date if soft deleted"
    )
    messages: Any = Field(..., description="Messages in the thread")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "thread-123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "deleted_at": None,
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
            }
        }


class ThreadListResponse(BaseModel):
    """Response schema for thread list."""

    threads: List[ThreadResponse] = Field(..., description="List of threads")

    class Config:
        json_schema_extra = {
            "example": {
                "threads": [
                    {
                        "id": "thread-123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "user-123e4567-e89b-12d3-a456-426614174000",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "deleted_at": None,
                    }
                ],
            }
        }

class ThreadUsageResponse(BaseModel):
    """Thread usage statistics schema."""

    thread_id: str = Field(..., description="Thread ID")
    user_id: str = Field(..., description="User ID who owns the thread")
    usage_metadata: CustomUsageMetadata | None = Field(
        ..., description="Total number of tokens used in the thread"
    )
    created_at: datetime = Field(..., description="Thread creation date")
    updated_at: datetime = Field(..., description="Last update date")

    est_cost: float = Field(0.0, description="Estimated cost based on token usage")
    est_cost_vnd: float = Field(0.0, description="Estimated cost in VND")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "thread_id": "thread-123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-123e4567-e89b-12d3-a456-426614174000",
                "usage_metadata": {
                    "input_tokens": 1500,
                    "output_tokens": 3000,
                    "total_tokens": 4500,
                    "input_token_details": {},
                    "output_token_details": {},
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }