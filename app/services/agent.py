from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig
from psycopg import AsyncConnection
from psycopg.rows import DictRow

from app.core.agent import CustomAgentState, aget_agent


class AgentService:
    def __init__(self, conn: AsyncConnection[DictRow]):
        self.conn = conn

    async def aget_history_chat(self, thread_id: str) -> list[CustomAgentState]:
        """Get historical chat messages for a thread."""

        config = RunnableConfig(configurable={"thread_id": thread_id})
        agent = aget_agent(self.conn)
        history = []
        async for state in agent.aget_state_history(config=config):
            history.append(state)
        return history


    async def aget_agent_response(
        self,
        user_name: str,
        user_input: str,
        thread_id: str,
    ) -> str:
        """Get agent response to user input."""
        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=3,
        )
        input = CustomAgentState(
            user_name=user_name,
            messages=[HumanMessage(content=user_input)],
        )
        agent = aget_agent(self.conn)
        responses = await agent.ainvoke(
            input=input,
            config=config,
            print_mode=["debug"],
        )
        await self.conn.commit()

        print(responses)
        return f"Agent response for: {user_input}"
