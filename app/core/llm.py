from functools import lru_cache

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config.settings import SETTINGS


@lru_cache
def get_llm() -> ChatOpenAI:
    """Cached LLM instance."""
    return ChatOpenAI(
        model=SETTINGS.openai_chat_model,
        api_key=SecretStr(SETTINGS.openai_api_key),
        temperature=0.9,
        streaming=True,
        stream_usage=True,
        use_responses_api=True,
        # reasoning={
        #     "effort": "low",  # can be "low", "medium", or "high"
        #     "summary": "concise",  # can be "auto", "concise", or "detailed"
        # },
        # verbosity="low",
        output_version="responses/v1",
        max_completion_tokens=1024,
    )
