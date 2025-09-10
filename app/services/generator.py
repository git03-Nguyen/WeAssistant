"""Response generation service with RAG chains."""

from functools import cached_property
from typing import List, Optional, Tuple, Union

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.callbacks import StdOutCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config.settings import get_settings
from app.models.intent import IntentType
from app.services.classifier import IntentResult
from app.services.rag import RAGService
from app.services.sessions import HistoryManager

TRIVIAL_RESPONSES = {
    "greeting": "Hi! I'm WeMasterTrade's assistant. I can help with trading FAQs or recommend prop-trading packages. How can I assist you?",
    "thanks": "You're welcome! Need help with anything else about WMT's prop-trading services?",
    "goodbye": "Goodbye! Feel free to return for trading guidance or package recommendations.",
}


class ResponseGeneratorService:
    """Generate responses using RAG chains and cached responses."""

    def __init__(
        self, rag_service: Optional[RAGService], history_manager: HistoryManager
    ):
        self.rag_service = rag_service
        self.history_manager = history_manager
        self.settings = get_settings()

    @cached_property
    def llm(self) -> ChatOpenAI:
        """Cached LLM instance."""
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        return ChatOpenAI(
            model=self.settings.openai_chat_model,
            api_key=SecretStr(self.settings.openai_api_key),
            temperature=0,  # Deterministic results enable OpenAI's automatic caching
        )

    @cached_property
    def faq_chain(self) -> Optional[Runnable]:
        """Cached FAQ RAG chain."""
        if not self.rag_service:
            return None

        try:
            return self._create_rag_chain("faq")
        except Exception as e:
            print(f"Warning: FAQ chain setup failed: {e}")
            return None

    @cached_property
    def consultant_chain(self) -> Optional[Runnable]:
        """Cached consultant RAG chain."""
        if not self.rag_service:
            return None

        try:
            return self._create_rag_chain("consultant")
        except Exception as e:
            print(f"Warning: Consultant chain setup failed: {e}")
            return None

    def _create_rag_chain(self, chain_type: str) -> Runnable:
        """Create RAG chain for specific type."""
        if not self.rag_service or not hasattr(self.rag_service, "vector_store"):
            raise ValueError("RAG service or vector store not available")

        retriever = self.rag_service.vector_store.as_retriever()

        # Chain-specific prompts
        if chain_type == "faq":
            system_prompt = """You are WeMasterTrade's (WMT) FAQ assistant. Answer trading questions using provided context only.
If context insufficient, say "Please contact WMT support for detailed information."
Keep responses concise, accurate, educational.

Context: {context}

Chat History: {chat_history}

Question: {input}"""
        else:  # consultant
            system_prompt = """You are WeMasterTrade's package consultant. Recommend suitable prop-trading packages based on user needs and provided context.
Match user experience/goals to appropriate packages. Be helpful, not pushy.
If unclear, ask clarifying questions about experience level and trading goals.

Context: {context}

Chat History: {chat_history}

Question: {input}"""

        qa_prompt = ChatPromptTemplate.from_template(system_prompt)
        self.llm.bind_tools(
            tools=[retriever.as_tool()],
            tool_choice="auto",
        )
        qa_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        return create_retrieval_chain(retriever, qa_chain)

    async def generate_response(
        self,
        message: Union[str, BaseMessage],
        intent_result: IntentResult,
        thread_id: str,
    ) -> Tuple[str, List[BaseMessage]]:
        """Generate response and return any additional messages that were created."""
        intent = intent_result.intent
        additional_messages = []

        # Extract message content if it's a BaseMessage and ensure it's a string
        if isinstance(message, BaseMessage):
            message_content = str(message.content) if message.content else ""
        else:
            message_content = str(message)

        if intent == IntentType.TRIVIAL:
            response_type = (
                intent_result.metadata.get("type", "greeting")
                if intent_result.metadata
                else "greeting"
            )
            response = TRIVIAL_RESPONSES.get(
                response_type, TRIVIAL_RESPONSES["greeting"]
            )
            return response, additional_messages

        elif intent == IntentType.FAQ and self.faq_chain:
            response = await self._invoke_chain(
                self.faq_chain, message_content, thread_id, intent
            )
            return response, additional_messages

        elif intent == IntentType.CONSULTANT and self.consultant_chain:
            response = await self._invoke_chain(
                self.consultant_chain, message_content, thread_id, intent
            )
            return response, additional_messages

        elif intent == IntentType.OTHER:
            response = "I can only assist with WeMasterTrade's prop-trading services, FAQs, and package recommendations. Please ask about trading or our services."
            return response, additional_messages

        else:
            # Fallback response inline
            if intent == IntentType.CONSULTANT:
                return (
                    "I'd love to recommend a suitable prop-trading package. Could you share your trading experience and goals?",
                    additional_messages,
                )
            elif intent == IntentType.FAQ:
                return (
                    "Please see our FAQ section at https://faq.wemastertrade.com or contact WMT support for detailed information.",
                    additional_messages,
                )
            else:
                return (
                    "I'm having trouble accessing information right now. Please try again or contact WMT support for assistance.",
                    additional_messages,
                )

    async def _invoke_chain(
        self,
        chain: Runnable,
        message_content: str,
        thread_id: str,
        intent: IntentType,
    ) -> str:
        """Invoke a RAG chain and return the response."""
        try:
            # Get chat history for this thread
            chat_history = await self.history_manager.get_thread_messages(thread_id)

            # Invoke chain and capture full response with debug config
            chain_input = {"input": message_content, "chat_history": chat_history}

            config: RunnableConfig = {
                "callbacks": [StdOutCallbackHandler()],
                "tags": [f"thread-{thread_id}", f"intent-{intent.value}"],
                "metadata": {
                    "thread_id": thread_id,
                    "intent": intent.value,
                    "message_length": len(message_content),
                    "history_length": len(chat_history),
                },
                "run_name": f"RAG_Chain_{intent.value}",
            }

            # Invoke with debug configuration
            result = await chain.ainvoke(chain_input, config=config)
            print(f"RAG chain result: {result}")

            return result["answer"]

        except Exception:
            # Inline fallback instead of method call
            if intent == IntentType.CONSULTANT:
                return "I'd love to recommend a suitable prop-trading package. Could you share your trading experience and goals?"
            else:
                return "I'm having trouble accessing information right now. Please try again or contact WMT support for assistance."
