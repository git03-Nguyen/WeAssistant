"""Main chat orchestrator coordinating all services."""

from typing import Dict, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.intent import IntentType
from app.models.thread import Thread
from app.schemas.chat import ChatRequest
from app.services.classifier import IntentClassifierService
from app.services.generator import ResponseGeneratorService
from app.services.moderator import ModeratorService
from app.services.rag import RAGService
from app.services.sessions import HistoryManager


class ChatOrchestrator:
    """Main orchestrator for streamlined chat pipeline."""

    def __init__(self, session: AsyncSession, rag_service: Optional[RAGService] = None):
        self.session = session

        # Initialize services
        self.moderator = ModeratorService()
        self.intent_classifier = IntentClassifierService()
        self.history_manager = HistoryManager(session)
        self.response_generator = ResponseGeneratorService(
            rag_service, self.history_manager
        )

    async def process_chat(self, request: ChatRequest) -> Dict:
        """Process chat with streamlined pipeline."""
        try:
            # Step 1: Get or create thread
            thread = await self._get_or_create_thread(request)
            user_message = HumanMessage(content=request.message)

            # Step 2: Check content safety first
            is_safe = await self.moderator.is_content_safe(request.message)
            if not is_safe:
                assistant_response = (
                    "I cannot process that request. Please ensure your message "
                    "follows our community guidelines."
                )
                assistant_message = AIMessage(content=assistant_response)
                intent = IntentType.OTHER
                confidence = 1.0
                additional_messages = []
            else:
                # Step 3: Classify intent and generate response
                intent_result = await self.intent_classifier.classify_intent(
                    request.message
                )
                (
                    assistant_response,
                    additional_messages,
                ) = await self.response_generator.generate_response(
                    user_message, intent_result, thread.id
                )
                assistant_message = AIMessage(content=assistant_response)
                intent = intent_result.intent
                confidence = intent_result.confidence

            # Step 4: Save all messages together
            all_messages = [user_message] + additional_messages + [assistant_message]
            await self.history_manager.add_messages(thread.id, all_messages)
            await self.session.commit()

            return self._create_response(
                thread.id, assistant_message, intent, confidence
            )

        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_thread_history(
        self, thread_id: str, limit: Optional[int] = None
    ) -> list[BaseMessage]:
        """Get thread history for API responses."""
        try:
            messages = await self.history_manager.get_thread_messages(thread_id, limit)
            return messages
        except Exception as e:
            raise DatabaseError(f"Failed to get thread history: {e}")

    async def _get_or_create_thread(self, request: ChatRequest) -> Thread:
        """Get existing thread or create new one."""
        if request.thread_id:
            thread = await self.session.get(Thread, request.thread_id)
            if not thread:
                raise ValueError(f"Thread {request.thread_id} not found")
            return thread
        else:
            if not request.user_id:
                raise ValueError("user_id is required when creating a new thread")

            thread = Thread(user_id=request.user_id)
            self.session.add(thread)
            await self.session.flush()
            return thread

    def _create_response(
        self,
        thread_id: str,
        assistant_message: AIMessage,
        intent: IntentType,
        confidence: float,
    ) -> Dict:
        """Create standardized response format."""
        return {
            "thread_id": thread_id,
            "assistant_message": {
                "content": assistant_message.content,
                "type": "ai",
            },
            "intent": intent.value,  # Convert enum to string for API response
            "confidence": confidence,
            "profile_used": None,
        }
