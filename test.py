import asyncio
import sys

from langchain.agents.react_agent import create_agent

from app.core.agent import SYSTEM_PROMPT, post_model_hook, pre_model_hook
from app.core.llm import get_llm
from app.core.state import HistoryMessageState
from app.core.vector_store import retrieve_context
from app.utils.database import open_db_connections

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_agent():
    return create_agent(
        model=get_llm(),
        tools=[retrieve_context],
        state_schema=HistoryMessageState,
        prompt=SYSTEM_PROMPT,
        name="WeAssistant Agent",
        pre_model_hook=pre_model_hook,
        post_model_hook=post_model_hook,
    )


asyncio.run(open_db_connections())

# Global agent object
agent = get_agent()
