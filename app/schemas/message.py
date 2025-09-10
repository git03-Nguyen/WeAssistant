"""Message-related Pydantic schemas for BaseMessage types."""


from pydantic import BaseModel, Field


class BaseMessageResponse(BaseModel):
    """Base response schema for LangChain BaseMessage types."""

    content: str = Field(..., description="The actual message content")
    type: str = Field(
        ...,
        description="Type of message, e.g., 'human', 'ai', 'system'",
        examples=["human", "ai", "system"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hello, can you help me?",
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
                        "type": "human",
                    },
                    {
                        "content": "Of course! How can I assist you today?",
                        "type": "ai",
                    },
                ],
                "total": 2,
            }
        }
