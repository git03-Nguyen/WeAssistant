"""Message-related Pydantic schemas for BaseMessage types."""

from typing import Literal

from pydantic import BaseModel, Field


class BaseMessageResponse(BaseModel):
    """Base response schema for LangChain BaseMessage types."""

    content: str = Field(..., description="The actual message content")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Role of the message sender"
    )
    type: Literal["human", "ai", "system", "tool", "function"] = Field(
        ..., description="LangChain message type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hello, can you help me?",
                "role": "user",
                "type": "human",
            }
        }


class MessageListResponse(BaseModel):
    """Response schema for message list from chat history."""

    messages: list[BaseMessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "content": "Hello, can you help me?",
                        "role": "user",
                        "type": "human",
                    },
                    {
                        "content": "Of course! How can I assist you today?",
                        "role": "assistant",
                        "type": "ai",
                    },
                ],
                "total": 2,
            }
        }
