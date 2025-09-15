"""Message management endpoints with orchestrated service."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_message_service
from app.schemas.message import HistoryMessageResponse, HistoryMessagesResponse
from app.services.messages import MessageService

router = APIRouter()


@router.get("/messages/{thread_id}", response_model=HistoryMessagesResponse)
async def get_all_messages(
    thread_id: str,
    *,
    message_service: MessageService = Depends(get_message_service),
) -> HistoryMessagesResponse:
    """Get all messages for a thread."""
    try:
        messages = await message_service.aget_messages(thread_id=thread_id)
        return HistoryMessagesResponse(
            messages=[
                HistoryMessageResponse.model_validate(message) for message in messages
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
