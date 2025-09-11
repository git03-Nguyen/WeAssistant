from langchain.agents import AgentState, create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver


class CustomAgentState(AgentState):
    user_id: str


agent = create_agent(
    "openai:gpt-5",
    [],
    state_schema=CustomAgentState,
    checkpointer=InMemorySaver(),
)


DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    agent = create_agent(
        "openai:gpt-5",
        [],
        checkpointer=checkpointer,
    )
