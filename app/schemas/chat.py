"""Chat-related Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.message import BaseMessageResponse


class ChatRequest(BaseModel):
    """Chat request schema."""

    thread_id: Optional[str] = Field(
        default=None,
        description="Thread ID for conversation context. If not provided, a new thread will be created.",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalized responses. Required if thread_id is not provided.",
    )
    message: str = Field(..., min_length=1, max_length=1000, description="User message")

    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "thread-123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user-123e4567-e89b-12d3-a456-426614174000",
                "message": "How can I start trading?",
            }
        }


class ChatResponse(BaseModel):
    """Chat response schema."""

    thread_id: str = Field(
        ..., description="Thread ID where the conversation is happening"
    )
    user_message: BaseMessageResponse = Field(
        ..., description="The user's message that was saved"
    )
    assistant_message: BaseMessageResponse = Field(
        ..., description="The assistant's response message"
    )
    intent: str = Field(..., description="Detected user intent")
    confidence: float = Field(..., ge=0, le=1, description="Intent confidence score")
    profile_used: Optional[str] = Field(
        default=None, description="User profile classification if applicable"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "thread-123e4567-e89b-12d3-a456-426614174000",
                "user_message": {
                    "content": "How can I start trading?",
                    "role": "user",
                    "type": "human",
                },
                "assistant_message": {
                    "content": "To start trading, you should first educate yourself about the markets...",
                    "role": "assistant",
                    "type": "ai",
                },
                "intent": "FAQ",
                "confidence": 0.95,
                "profile_used": "newbie",
            }
        }
