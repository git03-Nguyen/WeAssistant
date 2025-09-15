import operator
from datetime import datetime
from typing import Annotated, Optional, cast

from langchain.agents.react_agent import AgentState
from langchain_core.messages import BaseMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.utils.usage import _dict_int_op
from langgraph.graph.message import add_messages

# class AIResponse(BaseModel):
#     """Structured response format for AI messages."""

#     text: str = Field(description="The text content of the response")
#     sources: Optional[list[str]] = Field(
#         description="List of retrieve_context sources for the response if any",
#     )

#     class Config:
#         extra = "forbid"

class CustomUsageMetadata(UsageMetadata):
    """Custom UsageMetadata to allow default initialization."""

    timestamp: int


def add_usage(
    left: Optional[CustomUsageMetadata],
    right: Optional[CustomUsageMetadata],
) -> CustomUsageMetadata:
    """Recursively add two UsageMetadata objects, but only if they are different."""
    if not (left or right):
        return CustomUsageMetadata(
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            timestamp=int(datetime.now().timestamp()),
        )
    if not (left and right):
        return cast("CustomUsageMetadata", left or right)

    left_ts = left.get("timestamp", -1)
    right_ts = right.get("timestamp", -1)
    if left_ts != -1 and right_ts != -1:
        if left_ts >= right_ts:
            return cast("CustomUsageMetadata", left)
        else:
            return cast("CustomUsageMetadata", right)

    merged = CustomUsageMetadata(
        **cast(
            "CustomUsageMetadata",
            _dict_int_op(
                cast("dict", left),
                cast("dict", right),
                operator.add,
            ),
        ),
    )
    merged["timestamp"] = int(datetime.now().timestamp())
    return merged

class HistoryMessageState(AgentState):
    """State schema for historical messages."""

    history_messages: Annotated[list[BaseMessage], add_messages]

    token_usage: Annotated[Optional[CustomUsageMetadata], add_usage]
