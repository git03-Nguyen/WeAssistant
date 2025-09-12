"""Chat-related Pydantic schemas."""


from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request schema."""

    thread_id: str | None = Field(
        default=None,
        description="Thread ID for conversation context. If not provided, a new thread will be created.",
    )
    user_id: str = Field(
        ...,
        description="User ID for personalized responses and context",
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
    messages: list[BaseMessage] = Field(
        ..., description="The assistant's response messages"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "thread-123e4567-e89b-12d3-a456-426614174000",
                "messages": [
                    {
                        "type": "ai",
                        "content": "To start trading, you should first educate yourself about the markets...",
                    },
                ],
            }
        }
