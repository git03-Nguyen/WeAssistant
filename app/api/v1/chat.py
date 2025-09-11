"""Streamlined chat endpoints with orchestrated pipeline."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_agent_service, get_thread_service
from app.api.v1.users import get_user_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.message import BaseMessageResponse
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
            user_name=user.name,
            thread_id=thread_id,
            user_input=request.message,
        )

        return ChatResponse(
            thread_id=thread.id,
            messages=[BaseMessageResponse(type="ai", content=responses)],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# @router.post("/chat/stream")
# async def chat_stream(
#     request: ChatRequest,
# ):
#     """Process chat with streaming response (Server-Sent-Event API)."""

#     async def generate_chat_stream() -> AsyncGenerator[str, None]:
#         pass
