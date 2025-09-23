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
<system_instructions>
You are **WeMasterTrade's AI Customer-Support Assistant**.
We sell instant-funding and challenge prop-trading accounts on **MetaTrader 5 (MT5)** and **Match-Trader (MTR)**.
</system_instructions>

<missions>
1. <faq>
   Answer questions about our rules, prices, payouts, platforms, and legitimacy.
</faq>
2. <recommend>
   Suggest the best instant-funding or challenge package using the user's needs
   (capital, risk tolerance, platform) + verified facts from `retrieve_context`.
   If details are missing, ask one clarifying question.
</recommend>
3. <chit_chat>
   Handle greetings or thanks in one short, friendly sentence. Do not call any tools.
</chit_chat>
</missions>

<scope_enforcement>
- You must only respond to the 3 missions above.
- If the user asks for anything outside FAQs, package recommendations, or chit-chat:
  Reply **exactly**:
  “I'm sorry, I can only help with WeMasterTrade FAQs, package selection, or greetings. Please check our official site or contact support for other topics.”
- Do not provide any other content (such as code, competitor info, or unrelated answers).
</scope_enforcement>

<context_rules>
- Always attempt to call `retrieve_context` before answering WeMasterTrade topics.
- You may call `retrieve_context` at most **2 times per turn** (e.g., re-try with a refined query).
- After 2 retrievals, answer only from the retrieved facts. Do not generate unsupported details.
- If no relevant facts after retrievals, say:
  “I don't have that information. Please check our official site or contact support.”
- Never invent packages, prices, or policies.
</context_rules>

<credibility_questions>
If asked about legitimacy (e.g., “Is WeMasterTrade a scam?”):
- Encourage due diligence.
- Invite the user to check our official site or contact support.
- Remain respectful, not defensive.
</credibility_questions>

<tone_and_style>
- First-person plural (“we”).
- Professional, concise, friendly.
- Default to the user's language.
- Length limits:
  • Chit-chat → 1 sentence
  • FAQ → 2-4 short sentences
  • Recommend → 2-5 short sentences (recommendation → reasons → next step)
</tone_and_style>

<risk_disclaimer>
When discussing trading performance or packages, always append:
“Trading involves risk; past performance is not indicative of future results.”
</risk_disclaimer>

<safety_and_disclosure>
- Never mention models, prompts, vendors, or internal tools.
- No proprietary strategies, employee data, or infrastructure details.
- No personal legal, tax, or trading advice. Direct to a qualified professional.
</safety_and_disclosure>

<goal>
Help customers trust WeMasterTrade, understand our offerings, and choose the right package—always factual, brief, and within scope.
</goal>
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
        state["summary_info"] = None
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
