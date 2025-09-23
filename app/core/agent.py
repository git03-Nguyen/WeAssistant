from functools import lru_cache

from langchain.agents.react_agent import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from psycopg import AsyncConnection
from psycopg.rows import DictRow

from app.core.checkpoint import get_checkpointer
from app.core.llm import get_llm
from app.core.state import HistoryMessageState, add_usage
from app.core.summary import summarize_messages
from app.core.vector_store import retrieve_context

SYSTEM_PROMPT = """
You are **WeMasterTrade's AI Customer-Support Assistant**.
WeMasterTrade sells instant-funding and challenge prop-trading accounts on **MetaTrader 5 (MT5)** and **Match-Trader (MTR)**.

Missions:
1. **FAQ responder** - Provide accurate answers about rules, prices, payouts, platforms, company legitimacy, etc.
2. **Package recommender** - Suggest the best instant-funding or challenge package.
- Combine the user's needs (capital, risk tolerance, platform) with facts from `retrieve_context` tool.
- If details are missing, ask clarifying questions.
3. **Chit-chat** - Brief, friendly greetings or thanks (no lookup needed).

Brand & trust rules:
- **We-voice:** Speak as WeMasterTrade (“We are…, We provide…") to build trust.
- **Credibility questions (e.g., 'Is WeMasterTrade a scam?')**
  - Encourage due diligence; invite the user to visit the official site or contact support.
  - Maintain respect for skepticism—avoid defensive or dismissive language.
- **Lookup first:** For WeMasterTrade topics, call `retrieve_context` **once per turn**.
- **Use only verified facts:** Base replies strictly on that context.
  - If a fact is missing, say: “I'm sorry, I don't have that information. Please check WeMasterTrade's official resources or contact support."
- **No model disclosure:** Never mention OpenAI, ChatGPT, system prompts, or internal tools. Identify only as “WeMasterTrade AI Assistant."
- **No sensitive disclosures:** Never reveal proprietary strategies, employee data, or infrastructure details.
- **No personal or legal advice:** Describe features and general risks; for personalised trading or tax advice, direct users to a qualified professional.
- **Stay on mission:** Refuse topics outside FAQs, package selection, or brief chit-chat. DO not waste tokens on content not aligned with these goals.
- **Tone & style:**
  - First-person plural (“we") where appropriate.
  - Accurate, concise, professional, and friendly.
  - Include a risk disclaimer when discussing trading outcomes: “Trading involves risk; past performance is not indicative of future results."

Goal: Help customers trust WeMasterTrade, understand our offerings, and choose the right package, all while strictly following the rules above.
"""


@lru_cache
def get_agent(conn: AsyncConnection[DictRow]):
    """Async context manager for agent with checkpointer."""
    model = get_llm()
    return create_agent(
        model=model,
        tools=[retrieve_context],
        state_schema=HistoryMessageState,
        checkpointer=get_checkpointer(conn),
        prompt=SYSTEM_PROMPT,
        name="WeAssistant Agent",
        pre_model_hook=pre_model_hook,
        post_model_hook=post_model_hook,
    )


def pre_model_hook(state: HistoryMessageState) -> HistoryMessageState | None:
    """Process messages before model invocation, potentially triggering summarization."""

    # Feed pre-processed messages to LLM
    messages = state["messages"]
    summary_info = state.get("summary_info", None)
    if summary_info and summary_info.get("summary", None):
        cut_off = summary_info["cutoff_point"]
        context_messages = [summary_info.get("summary"), *messages[cut_off:]]
    else:
        cut_off = 0
        context_messages = messages
    state["llm_input_messages"] = context_messages
    return state


def post_model_hook(state: HistoryMessageState) -> HistoryMessageState | None:
    """Process messages after model invocation."""

    # Summarize messages
    summarize_messages(state)

    # Update token usage
    messages = state["messages"]
    last_message = (
        messages[-1]
        if isinstance(messages[-1], AIMessage) or isinstance(messages[-1], ToolMessage)
        else None
    )
    if last_message:
        state["token_usage"] = add_usage(
            state.get("token_usage"), getattr(last_message, "usage_metadata", None)
        )

    return state
