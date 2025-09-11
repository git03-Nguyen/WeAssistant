from functools import lru_cache

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config.settings import SETTINGS


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """Cached LLM instance."""
    if not SETTINGS.openai_api_key:
        raise ValueError("OpenAI API key is required")

    return ChatOpenAI(
        # async_client=
        model=SETTINGS.openai_chat_model,
        api_key=SecretStr(SETTINGS.openai_api_key),
        temperature=1,
        streaming=True,
        stream_usage=True,
        use_responses_api=True,
        include_response_headers=True,
        reasoning={
            "effort": "low",  # can be "low", "medium", or "high"
            "summary": "auto",  # can be "auto", "concise", or "detailed"
        },
        verbosity="low",
        output_version="responses/v1",
        verbose=True,
    )
