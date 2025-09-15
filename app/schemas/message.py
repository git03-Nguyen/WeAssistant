"""Message-related Pydantic schemas for BaseMessage types."""


from datetime import datetime

from pydantic import BaseModel, Field


class HistoryMessageResponse(BaseModel):
    """Base response schema for LangChain BaseMessage types."""

    content: str = Field(..., description="The actual message content")
    type: str = Field(
        ...,
        description="Type of message, e.g., 'human', 'ai', 'system'",
        examples=["human", "ai", "system", "tool"],
    )
    created_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the message was created",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hello, can you help me?",
                "type": "human",
            }
        }

class HistoryMessagesResponse(BaseModel):
    """Response schema for a list of history messages."""

    messages: list[HistoryMessageResponse] = Field(..., description="List of messages")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "content": "Hello, can you help me?",
                        "type": "human",
                        "created_date": "2024-01-15T10:30:00Z",
                    },
                    {
                        "content": "Sure! What do you need assistance with?",
                        "type": "ai",
                        "created_date": "2024-01-15T10:31:00Z",
                    },
                ]
            }
        }