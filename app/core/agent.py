from functools import lru_cache

from langchain.agents.middleware import SummarizationMiddleware
from langchain.agents.react_agent import create_agent
from langchain_openai import ChatOpenAI
from psycopg import AsyncConnection
from psycopg.rows import DictRow
from pydantic import SecretStr

from app.config.settings import SETTINGS
from app.core.checkpoint import get_checkpointer
from app.core.vector_store import retrieve_context


@lru_cache
def _get_llm() -> ChatOpenAI:
    """Cached LLM instance."""
    return ChatOpenAI(
        model=SETTINGS.openai_chat_model,
        api_key=SecretStr(SETTINGS.openai_api_key),
        temperature=1,
        streaming=True,
        stream_usage=True,
        use_responses_api=True,
        reasoning={
            "effort": "low",  # can be "low", "medium", or "high"
            "summary": "auto",  # can be "auto", "concise", or "detailed"
        },
        verbosity="low",
        output_version="responses/v1",
    )


@lru_cache
def aget_agent(conn: AsyncConnection[DictRow]):
    """Async context manager for agent with checkpointer."""
    model = _get_llm()
    return create_agent(
        model=model,
        tools=[retrieve_context],
        # state_schema=CustomAgentState,
        checkpointer=get_checkpointer(conn),
        prompt="You are a helpful AI assistant.",
        name="WeAssistant Agent",
        # response_format=ProviderStrategy()
        middleware=[
            SummarizationMiddleware(
                model=model,
                max_tokens_before_summary=SETTINGS.summary_max_context_token,
                messages_to_keep=SETTINGS.summary_max_message_count,
                # summary_prompt="Custom prompt for summarization...",
            ),
        ],
    )
