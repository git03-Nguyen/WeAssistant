from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig

from app.core.agent import CustomAgentState, aget_agent


class AgentService:
    async def aget_history_chat(self, thread_id: str) -> list[CustomAgentState]:
        """Get historical chat messages for a thread."""

        async with aget_agent() as agent:
            async for state in agent.aget_state_history(
                config=RunnableConfig(
                    configurable={"thread_id": thread_id},
                )
            ):
                print(state)

        return []

    async def aget_agent_response(
        self,
        user_name: str,
        user_input: str,
        thread_id: str,
    ) -> str:
        """Get agent response to user input."""
        async with aget_agent() as agent:
            responses = await agent.ainvoke(
                input=CustomAgentState(
                    user_name=user_name,
                    messages=[HumanMessage(content=user_input)],
                ),
                config=RunnableConfig(
                    configurable={"thread_id": thread_id},
                    recursion_limit=3,
                ),
                print_mode=["debug"],
            )

            print(responses)
            return f"Agent response for: {user_input}"
