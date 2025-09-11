"""Message-related Pydantic schemas for BaseMessage types."""


from pydantic import BaseModel, Field


class BaseMessageResponse(BaseModel):
    """Base response schema for LangChain BaseMessage types."""

    content: str = Field(..., description="The actual message content")
    type: str = Field(
        ...,
        description="Type of message, e.g., 'human', 'ai', 'system'",
        examples=["human", "ai", "system", "tool"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Hello, can you help me?",
                "type": "human",
            }
        }
