from pprint import pprint

from langchain.agents import AgentState
from langchain_core.callbacks import (
    get_usage_metadata_callback,
)
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage
from langchain_core.messages.utils import convert_to_messages
from langchain_core.runnables.config import RunnableConfig
from psycopg import AsyncConnection
from psycopg.rows import DictRow

from app.core.agent import aget_agent


class AgentService:
    def __init__(self, conn: AsyncConnection[DictRow]):
        self.conn = conn

    async def aget_history_chat(self, thread_id: str):
        """Get the historical chat message for a thread."""

        config = RunnableConfig(configurable={"thread_id": thread_id})
        agent = aget_agent(self.conn)
        async for state in agent.aget_state_history(config=config):
            return convert_to_messages(state.values["messages"])

        return []

    async def aget_agent_response(
        self,
        user_name: str,
        user_input: str,
        thread_id: str,
    ) -> BaseMessage | None:
        """Get agent response to user input."""

        with get_usage_metadata_callback() as usage_callback:
            config = RunnableConfig(
                configurable={"thread_id": thread_id},
                recursion_limit=3,
                callbacks=[usage_callback],
            )
            input = self._create_new_state(user_name, user_input)
            agent = aget_agent(self.conn)
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

    def _create_new_state(self, user_name: str, user_input: str) -> AgentState:
        return {
            "messages": [HumanMessage(content=user_input)],
        }