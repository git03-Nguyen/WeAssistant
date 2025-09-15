"""Summarization middleware."""

import uuid
from collections.abc import Callable, Iterable, Sequence
from typing import Optional, Tuple, cast

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    MessageLikeRepresentation,
    RemoveMessage,
    ToolMessage,
)
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_openai import ChatOpenAI
from langgraph.graph.message import (
    REMOVE_ALL_MESSAGES,
)

from app.config.settings import SETTINGS
from app.core.llm import get_llm
from app.core.state import CustomUsageMetadata, HistoryMessageState, add_usage

TokenCounter = Callable[[Iterable[MessageLikeRepresentation]], int]

DEFAULT_SUMMARY_PROMPT = """<role>
Context Extraction Assistant
</role>

<primary_objective>
Your sole objective in this task is to extract the highest quality/most relevant context from the conversation history below.
</primary_objective>

<objective_information>
You're nearing the total number of input tokens you can accept, so you must extract the highest quality/most relevant pieces of information from your conversation history.
This context will then overwrite the conversation history presented below. Because of this, ensure the context you extract is only the most important information to your overall goal.
</objective_information>

<instructions>
The conversation history below will be replaced with the context you extract in this step. Because of this, you must do your very best to extract and record all of the most important context from the conversation history.
You want to ensure that you don't repeat any actions you've already completed, so the context you extract from the conversation history should be focused on the most important information to your overall goal.
</instructions>

The user will message you with the full message history you'll be extracting context from, to then replace. Carefully read over it all, and think deeply about what information is most important to your overall goal that should be saved:

With all of this in mind, please carefully read over the entire conversation history, and extract the most important and relevant context to replace it so that you can free up space in the conversation history.
Respond ONLY with the extracted context. Do not include any additional information, or text before or after the extracted context.

<messages>
Messages to summarize:
{messages}
</messages>"""

SUMMARY_PREFIX = "## Previous conversation summary:"

_DEFAULT_TRIM_TOKEN_LIMIT = 2500
_DEFAULT_FALLBACK_MESSAGE_COUNT = 15
_SEARCH_RANGE_FOR_TOOL_PAIRS = 5

max_tokens_before_summary = 3000
messages_to_keep = SETTINGS.summary_max_message_count
summary_prompt = DEFAULT_SUMMARY_PROMPT
summary_prefix = SUMMARY_PREFIX


def summarize_messages(state: HistoryMessageState) -> HistoryMessageState | None:
    """Process messages before model invocation, potentially triggering summarization."""
    messages = state["messages"]
    _ensure_message_ids(messages)

    total_tokens = count_tokens_approximately(messages)
    if (
        max_tokens_before_summary is not None
        and total_tokens < max_tokens_before_summary
    ):
        return None

    cutoff_index = _find_safe_cutoff(messages)

    if cutoff_index <= 0:
        return None

    messages_to_summarize, preserved_messages = _partition_messages(
        messages, cutoff_index
    )

    summary, usage_metadata = _create_summary(get_llm(), messages_to_summarize)
    new_messages = _build_new_messages(summary)

    state["messages"] = [
        RemoveMessage(id=REMOVE_ALL_MESSAGES),
        *new_messages,
        *preserved_messages,
    ]

    state["token_usage"] = add_usage(state.get("token_usage"), usage_metadata)
    return state


def _build_new_messages(summary: str) -> list[HumanMessage]:
    return [
        HumanMessage(
            content=f"Here is a summary of the conversation to date:\n\n{summary}"
        )
    ]


def _ensure_message_ids(messages: Sequence[BaseMessage]) -> None:
    """Ensure all messages have unique IDs for the add_messages reducer."""
    for msg in messages:
        if msg.id is None:
            msg.id = str(uuid.uuid4())


def _partition_messages(
    conversation_messages: Sequence[BaseMessage],
    cutoff_index: int,
) -> tuple[Sequence[BaseMessage], Sequence[BaseMessage]]:
    """Partition messages into those to summarize and those to preserve."""
    messages_to_summarize = conversation_messages[:cutoff_index]
    preserved_messages = conversation_messages[cutoff_index:]

    return messages_to_summarize, preserved_messages


def _find_safe_cutoff(messages: Sequence[BaseMessage]) -> int:
    """Find safe cutoff point that preserves AI/Tool message pairs.

    Returns the index where messages can be safely cut without separating
    related AI and Tool messages. Returns 0 if no safe cutoff is found.
    """
    if len(messages) <= messages_to_keep:
        return 0

    target_cutoff = len(messages) - messages_to_keep

    for i in range(target_cutoff, -1, -1):
        if _is_safe_cutoff_point(messages, i):
            return i

    return 0


def _is_safe_cutoff_point(messages: Sequence[BaseMessage], cutoff_index: int) -> bool:
    """Check if cutting at index would separate AI/Tool message pairs."""
    if cutoff_index >= len(messages):
        return True

    search_start = max(0, cutoff_index - _SEARCH_RANGE_FOR_TOOL_PAIRS)
    search_end = min(len(messages), cutoff_index + _SEARCH_RANGE_FOR_TOOL_PAIRS)

    for i in range(search_start, search_end):
        if not _has_tool_calls(messages[i]):
            continue

        tool_call_ids = _extract_tool_call_ids(cast("AIMessage", messages[i]))
        if _cutoff_separates_tool_pair(messages, i, cutoff_index, tool_call_ids):
            return False

    return True


def _has_tool_calls(message: BaseMessage) -> bool:
    """Check if message is an AI message with tool calls."""
    return (
        isinstance(message, AIMessage)
        and hasattr(message, "tool_calls")
        and message.tool_calls  # type: ignore[return-value]
    )


def _extract_tool_call_ids(ai_message: AIMessage) -> set[str]:
    """Extract tool call IDs from an AI message."""
    tool_call_ids = set()
    for tc in ai_message.tool_calls:
        call_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
        if call_id is not None:
            tool_call_ids.add(call_id)
    return tool_call_ids


def _cutoff_separates_tool_pair(
    messages: Sequence[BaseMessage],
    ai_message_index: int,
    cutoff_index: int,
    tool_call_ids: set[str],
) -> bool:
    """Check if cutoff separates an AI message from its corresponding tool messages."""
    for j in range(ai_message_index + 1, len(messages)):
        message = messages[j]
        if isinstance(message, ToolMessage) and message.tool_call_id in tool_call_ids:
            ai_before_cutoff = ai_message_index < cutoff_index
            tool_before_cutoff = j < cutoff_index
            if ai_before_cutoff != tool_before_cutoff:
                return True
    return False


def _create_summary(
    model: ChatOpenAI,
    messages_to_summarize: Sequence[BaseMessage],
) -> Tuple[str, Optional[CustomUsageMetadata]]:
    """Generate summary for the given messages."""
    if not messages_to_summarize:
        return "No previous conversation history.", None

    trimmed_messages = _trim_messages_for_summary(messages_to_summarize)
    if not trimmed_messages:
        return "Previous conversation was too long to summarize.", None

    try:
        response = model.invoke(summary_prompt.format(messages=trimmed_messages))
        summary_text = response.content[-1].get("text", "").strip()  # type: ignore
        usage_metadata = getattr(response, "usage_metadata", None)
        return summary_text, usage_metadata
    except Exception as e:  # noqa: BLE001
        return f"Error generating summary: {e!s}", None


def _trim_messages_for_summary(
    messages: Sequence[BaseMessage],
) -> Sequence[BaseMessage]:
    """Trim messages to fit within summary generation limits."""
    try:
        return trim_messages(
            messages,
            max_tokens=_DEFAULT_TRIM_TOKEN_LIMIT,
            token_counter=count_tokens_approximately,
            start_on="human",
            strategy="last",
            allow_partial=True,
            include_system=True,
        )
    except Exception:  # noqa: BLE001
        return messages[-_DEFAULT_FALLBACK_MESSAGE_COUNT:]
