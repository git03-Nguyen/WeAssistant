import asyncio
import sys

from langchain.agents.react_agent import create_agent

from app.core.agent import SYSTEM_PROMPT, post_model_hook, pre_model_hook
from app.core.state import HistoryMessageState
from app.core.vector_store import retrieve_context
from app.utils.database import open_db_connections

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from functools import lru_cache

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config.settings import SETTINGS


@lru_cache
def get_gpt_5_nano_llm() -> ChatOpenAI:
    """Cached LLM instance."""
    return ChatOpenAI(
        model="gpt-5-nano",
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
        max_completion_tokens=1024,
    )


def get_gpt_4_1_nano_llm() -> ChatOpenAI:
    """Cached LLM instance."""
    return ChatOpenAI(
        model="gpt-4.1-nano",
        api_key=SecretStr(SETTINGS.openai_api_key),
        temperature=1,
        streaming=True,
        stream_usage=True,
        use_responses_api=True,
        output_version="responses/v1",
        max_completion_tokens=1024,
    )


def get_gpt_5_nano_agent():
    return create_agent(
        model=get_gpt_5_nano_llm(),
        tools=[retrieve_context],
        state_schema=HistoryMessageState,
        prompt=SYSTEM_PROMPT,
        name="WeAssistant Agent",
        pre_model_hook=pre_model_hook,
        post_model_hook=post_model_hook,
    )


def get_gpt_4_1_nano_agent():
    return create_agent(
        model=get_gpt_4_1_nano_llm(),
        tools=[retrieve_context],
        state_schema=HistoryMessageState,
        prompt=SYSTEM_PROMPT,
        name="WeAssistant Agent",
        pre_model_hook=pre_model_hook,
        post_model_hook=post_model_hook,
    )


asyncio.run(open_db_connections())

# Global agent object
gpt_5_nano = get_gpt_5_nano_agent()
gpt_4_1_nano = get_gpt_4_1_nano_agent()
