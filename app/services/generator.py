"""Response generation service with RAG chains."""

from functools import cached_property, lru_cache
from typing import Optional

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from app.config.settings import get_settings
from app.models.intent import IntentType
from app.services.classifier import IntentResult
from app.services.rag import RAGService
from app.services.sessions import SessionManager


class ResponseGeneratorService:
    """Generate responses using RAG chains and cached responses."""

    def __init__(
        self, rag_service: Optional[RAGService], session_manager: SessionManager
    ):
        self.rag_service = rag_service
        self.session_manager = session_manager
        self.settings = get_settings()

    @cached_property
    def llm(self) -> ChatOpenAI:
        """Cached LLM instance."""
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        return ChatOpenAI(
            model=self.settings.openai_chat_model,
            temperature=0,  # Deterministic results enable OpenAI's automatic caching
        )

    @lru_cache(maxsize=1)
    def _get_trivial_responses(self) -> dict[str, str]:
        """Get cached trivial responses."""
        return {
            "greeting": "Hi! I'm WeMasterTrade's assistant. I can help with trading FAQs or recommend prop-trading packages. How can I assist you?",
            "thanks": "You're welcome! Need help with anything else about WMT's prop-trading services?",
            "goodbye": "Goodbye! Feel free to return for trading guidance or package recommendations.",
        }

    @cached_property
    def faq_chain(self) -> Optional[RunnableWithMessageHistory]:
        """Cached FAQ RAG chain."""
        if not self.rag_service:
            return None

        try:
            return self._create_rag_chain("faq")
        except Exception as e:
            print(f"Warning: FAQ chain setup failed: {e}")
            return None

    @cached_property
    def consultant_chain(self) -> Optional[RunnableWithMessageHistory]:
        """Cached consultant RAG chain."""
        if not self.rag_service:
            return None

        try:
            return self._create_rag_chain("consultant")
        except Exception as e:
            print(f"Warning: Consultant chain setup failed: {e}")
            return None

    def _create_rag_chain(self, chain_type: str) -> RunnableWithMessageHistory:
        """Create RAG chain for specific type."""
        if not self.rag_service or not hasattr(self.rag_service, "vector_store"):
            raise ValueError("RAG service or vector store not available")

        retriever = self.rag_service.vector_store.as_retriever()

        # Context prompt for history awareness
        contextualize_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Given chat history and latest question, formulate a standalone question. Do NOT answer, just reformulate if needed.",
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_prompt
        )

        # Chain-specific prompts
        if chain_type == "faq":
            system_prompt = """You are WeMasterTrade's (WMT) FAQ assistant. Answer trading questions using provided context only.
If context insufficient, say "Please contact WMT support for detailed information."
Keep responses concise, accurate, educational.

{context}"""
        else:  # consultant
            system_prompt = """You are WeMasterTrade's package consultant. Recommend suitable prop-trading packages based on user needs and provided context.
Match user experience/goals to appropriate packages. Be helpful, not pushy.
If unclear, ask clarifying questions about experience level and trading goals.

{context}"""

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        qa_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

        return RunnableWithMessageHistory(
            rag_chain,
            self.session_manager.get_session_history_sync,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    async def generate_response(
        self, message: str, intent_result: IntentResult, thread_id: str
    ) -> str:
        """Generate response based on intent."""
        intent = intent_result.intent

        if intent == IntentType.TRIVIAL:
            response_type = "greeting"
            if intent_result.metadata:
                response_type = intent_result.metadata.get("type", "greeting")
            return self._get_trivial_response(response_type)

        elif intent == IntentType.FAQ and self.faq_chain:
            try:
                result = await self.faq_chain.ainvoke(
                    {"input": message},
                    config={"configurable": {"thread_id": thread_id}},
                )
                return result["answer"]
            except Exception:
                return self._get_fallback_response(intent)

        elif intent == IntentType.CONSULTANT and self.consultant_chain:
            try:
                result = await self.consultant_chain.ainvoke(
                    {"input": message},
                    config={"configurable": {"thread_id": thread_id}},
                )
                return result["answer"]
            except Exception:
                return self._get_fallback_response(intent)

        elif intent == IntentType.OTHER:
            return "I can only assist with WeMasterTrade's prop-trading services, FAQs, and package recommendations. Please ask about trading or our services."

        else:
            return self._get_fallback_response(intent)

    def _get_trivial_response(self, response_type: str) -> str:
        """Get cached trivial response."""
        responses = self._get_trivial_responses()
        return responses.get(response_type, responses["greeting"])

    @lru_cache(maxsize=10)
    def _get_fallback_response(self, intent: IntentType) -> str:
        """Get cached fallback responses."""
        if intent == IntentType.CONSULTANT:
            return "I'd love to recommend a suitable prop-trading package. Could you share your trading experience and goals?"
        else:
            return "I'm having trouble accessing information right now. Please try again or contact WMT support for assistance."
