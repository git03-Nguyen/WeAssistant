"""Streamlined chat endpoints with orchestrated pipeline."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_agent_service, get_thread_service
from app.api.v1.users import get_user_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent import AgentService
from app.services.threads import ThreadService
from app.services.users import UserService

router = APIRouter()


@router.post("/chat/invoke", response_model=ChatResponse)
async def chat_restful(
    request: ChatRequest,
    *,
    user_service: UserService = Depends(get_user_service),
    thread_service: ThreadService = Depends(get_thread_service),
    agent_service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    """Process chat with streamlined pipeline."""
    try:
        user = await user_service.aget_user_profile(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if request.thread_id is None:
            thread = await thread_service.acreate_thread(user_id=request.user_id)
        else:
            thread = await thread_service.aget_thread(
                thread_id=request.thread_id,
                user_id=request.user_id,
            )
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

        thread_id = thread.id
        responses = await agent_service.aget_agent_response(
            thread_id=thread_id,
            user_input=request.message,
        )

        return ChatResponse(
            thread_id=thread.id,
            messages=[responses] if responses else [],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    *,
    user_service: UserService = Depends(get_user_service),
    thread_service: ThreadService = Depends(get_thread_service),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Process chat with streaming response (Server-Sent-Event API)."""
    try:
        user = await user_service.aget_user_profile(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if request.thread_id is None:
            thread = await thread_service.acreate_thread(user_id=request.user_id)
        else:
            thread = await thread_service.aget_thread(
                thread_id=request.thread_id,
                user_id=request.user_id,
            )
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

        thread_id = thread.id

        async def event_generator():
            try:
                async for message in agent_service.astream_agent_response(
                    user_input=request.message,
                    thread_id=thread_id,
                ):
                    yield f"data: {message}\n\n"
            except Exception as exc:
                # surface an SSE error so the front-end knows the stream broke
                yield f"data: {type(exc).__name__}: {exc}\n\n"
                raise

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
