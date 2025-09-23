from pprint import pprint
from typing import AsyncGenerator

from langchain_core.callbacks import (
    get_usage_metadata_callback,
)
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage
from langchain_core.messages.utils import convert_to_messages
from langchain_core.runnables.config import RunnableConfig
from psycopg import AsyncConnection
from psycopg.rows import DictRow

from app.core.agent import get_agent
from app.core.state import CustomUsageMetadata, HistoryMessageState


class AgentService:
    def __init__(self, conn: AsyncConnection[DictRow]):
        self.conn = conn

    async def aget_history_chat(self, thread_id: str):
        """Get the historical chat message for a thread."""

        config = RunnableConfig(configurable={"thread_id": thread_id})
        agent = get_agent(self.conn)
        async for state in agent.aget_state_history(config=config):
            return convert_to_messages(state.values["messages"])

        return []

    async def aget_agent_response(
        self,
        user_input: str,
        thread_id: str,
    ) -> BaseMessage | None:
        """Get agent response to user input."""

        with get_usage_metadata_callback() as usage_callback:
            config = RunnableConfig(
                configurable={"thread_id": thread_id},
                recursion_limit=25,
                callbacks=[usage_callback],
            )
            input = self._create_new_state(user_input)
            agent = get_agent(self.conn)
            responses = await agent.ainvoke(
                input=input,
                config=config,
            )
            await self.conn.commit()

            print("-------------------------------")
            pprint(usage_callback.usage_metadata)
            messages = responses.get("messages", [])
            last_message = convert_to_messages(messages)[-1]
            if isinstance(last_message, AIMessageChunk):
                return last_message
            if isinstance(last_message, AIMessage):
                return last_message
            return None

    async def astream_agent_response(
        self,
        user_input: str,
        thread_id: str,
    ) -> AsyncGenerator[AIMessageChunk, None]:
        """Stream agent response to user input."""

        with get_usage_metadata_callback() as usage_callback:
            config = RunnableConfig(
                configurable={"thread_id": thread_id},
                recursion_limit=25,
                callbacks=[usage_callback],
            )
            input = self._create_new_state(user_input)
            agent = get_agent(self.conn)
            async for responses in agent.astream(
                input=input,
                config=config,
                stream_mode="messages",
            ):
                chunk = responses[0]  # type: ignore
                if isinstance(chunk, AIMessageChunk):
                    yield chunk

            await self.conn.commit()
            print("-------------------------------")
            pprint(usage_callback.usage_metadata)

    def _create_new_state(self, user_input: str) -> HistoryMessageState:
        """Create a new agent state with the user's input."""
        return {
            "messages": [HumanMessage(content=user_input)],
            "summary_info": None,
            "token_usage": None,
        }

    async def aget_thread_usage(self, thread_id: str) -> CustomUsageMetadata | None:
        """Get token usage statistics for a thread."""
        agent = get_agent(self.conn)
        async for state in agent.aget_state_history(
            config=RunnableConfig(configurable={"thread_id": thread_id})
        ):
            usage = state.values["token_usage"]
            if usage:
                return usage
            else:
                return None