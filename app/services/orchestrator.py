"""Main chat orchestrator coordinating all services."""

import asyncio
from typing import Dict, Optional

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.intent import IntentType
from app.models.thread import Thread
from app.schemas.chat import ChatRequest
from app.services.classifier import IntentClassifierService
from app.services.generator import ResponseGeneratorService
from app.services.moderator import ModeratorService
from app.services.rag import RAGService
from app.services.sessions import SessionManager


class ChatOrchestrator:
    """Main orchestrator for streamlined chat pipeline."""

    def __init__(self, session: AsyncSession, rag_service: Optional[RAGService] = None):
        self.session = session

        # Initialize services
        self.moderator = ModeratorService()
        self.intent_classifier = IntentClassifierService()
        self.session_manager = SessionManager(session)
        self.response_generator = ResponseGeneratorService(
            rag_service, self.session_manager
        )

    async def process_chat(self, request: ChatRequest) -> Dict:
        """Process chat with streamlined pipeline."""
        try:
            # Step 1: Get or create thread
            thread = await self._get_or_create_thread(request)

            # Step 2: Parallel processing - Moderation & Intent Classification
            moderation_task = self.moderator.is_content_safe(request.message)
            intent_task = self.intent_classifier.classify_intent(request.message)

            # Wait for both to complete
            is_safe, intent_result = await asyncio.gather(moderation_task, intent_task)

            # Step 3: Save user message to chat history
            user_message = HumanMessage(content=request.message)
            await self.session_manager.add_messages(thread.id, [user_message])

            # Step 4: Handle moderation failure
            if not is_safe:
                assistant_response = (
                    "I cannot process that request. Please ensure your message "
                    "follows our community guidelines."
                )
                assistant_message = AIMessage(content=assistant_response)
                await self.session_manager.add_messages(thread.id, [assistant_message])
                await self.session.commit()

                return self._create_response(
                    thread.id, user_message, assistant_message, IntentType.OTHER, 1.0
                )

            # Step 5: Generate response based on intent
            assistant_response = await self.response_generator.generate_response(
                request.message, intent_result, thread.id
            )

            # Step 6: Save assistant message to chat history
            assistant_message = AIMessage(content=assistant_response)
            await self.session_manager.add_messages(thread.id, [assistant_message])
            await self.session.commit()

            # Clear cache for fresh data
            await self.session_manager.clear_cache(thread.id)

            return self._create_response(
                thread.id,
                user_message,
                assistant_message,
                intent_result.intent,
                intent_result.confidence,
            )

        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_thread_history(self, thread_id: str, limit: Optional[int] = None):
        """Get thread history for API responses."""
        try:
            messages = await self.session_manager.get_thread_messages(thread_id, limit)

            # Convert BaseMessage objects to response format
            formatted_messages = []
            for msg in messages:
                if hasattr(msg, "content"):
                    message_data = {
                        "content": msg.content,
                        "role": "user"
                        if msg.__class__.__name__ == "HumanMessage"
                        else "assistant",
                        "type": msg.__class__.__name__.lower().replace("message", ""),
                    }
                    formatted_messages.append(message_data)

            return {"messages": formatted_messages, "total": len(formatted_messages)}
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
        user_message: HumanMessage,
        assistant_message: AIMessage,
        intent: IntentType,
        confidence: float,
    ) -> Dict:
        """Create standardized response format."""
        return {
            "thread_id": thread_id,
            "user_message": {
                "role": "user",
                "content": user_message.content,
                "type": "human",
            },
            "assistant_message": {
                "role": "assistant",
                "content": assistant_message.content,
                "type": "ai",
            },
            "intent": intent.value,  # Convert enum to string for API response
            "confidence": confidence,
            "profile_used": None,
        }
