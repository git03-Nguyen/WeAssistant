"""Streamlined chat endpoints with orchestrated pipeline."""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_chat_orchestrator
from app.core.exceptions import WeAssistantException
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.message import MessageResponse
from app.services.orchestrator import ChatOrchestrator

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_restful(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> ChatResponse:
    """Process chat with streamlined pipeline (RESTful API)."""
    try:
        # Process chat using orchestrator
        result = await orchestrator.process_chat(request)

        return ChatResponse(
            thread_id=result["thread_id"],
            user_message=MessageResponse.model_validate(result["user_message"]),
            assistant_message=MessageResponse.model_validate(
                result["assistant_message"]
            ),
            intent=result["intent"],
            confidence=result["confidence"],
            profile_used=result["profile_used"],
        )

    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    """Process chat with streaming response (Server-Sent-Event API)."""

    async def generate_chat_stream() -> AsyncGenerator[str, None]:
        try:
            # Start processing indicators
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Processing with moderation and routing...'})}\n\n"

            # Process the chat request
            result = await orchestrator.process_chat(request)

            # Send thread info if new thread was created
            if not request.thread_id:
                yield f"data: {json.dumps({'type': 'thread_created', 'thread_id': result['thread_id']})}\n\n"

            # Send user message confirmation
            yield f"data: {json.dumps({'type': 'user_message', 'message': MessageResponse.model_validate(result['user_message']).model_dump()})}\n\n"

            # Send intent detection
            yield f"data: {json.dumps({'type': 'intent_detected', 'intent': result['intent'], 'confidence': result['confidence']})}\n\n"

            # Stream the assistant response word by word for better UX
            assistant_content = result["assistant_message"].content
            words = assistant_content.split()
            current_response = ""

            for i, word in enumerate(words):
                current_response += word + " "
                yield f"data: {json.dumps({'type': 'token', 'content': word, 'full_response': current_response.strip()})}\n\n"

                # Add small delay every few words for realistic streaming
                if i % 3 == 0:
                    import asyncio

                    await asyncio.sleep(0.05)

            # Send final completion message
            yield f"data: {json.dumps({'type': 'complete', 'assistant_message': MessageResponse.model_validate(result['assistant_message']).model_dump(), 'intent': result['intent'], 'confidence': result['confidence'], 'profile_used': result['profile_used']})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_chat_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )
