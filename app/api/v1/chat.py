"""Streamlined chat endpoints with orchestrated pipeline."""

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.message import BaseMessageResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_restful(
    request: ChatRequest,
) -> ChatResponse:
    """Process chat with streamlined pipeline (RESTful API)."""
    try:
        # Process chat using orchestrator
        return ChatResponse(
            thread_id="thread-id-placeholder",
            assistant_message=BaseMessageResponse(
                type="assistant",
                content="This is a placeholder response from the assistant.",
            ),
            intent="general",
            confidence=0.95,
            profile_used=None,
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
