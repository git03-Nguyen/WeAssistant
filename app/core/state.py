from typing import Annotated

from langchain.agents.react_agent import AgentState
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# class AIResponse(BaseModel):
#     """Structured response format for AI messages."""

#     text: str = Field(description="The text content of the response")
#     sources: Optional[list[str]] = Field(
#         description="List of retrieve_context sources for the response if any",
#     )

#     class Config:
#         extra = "forbid"


class HistoryMessageState(AgentState):
    """State schema for historical messages."""

    history_messages: Annotated[list[BaseMessage], add_messages]
