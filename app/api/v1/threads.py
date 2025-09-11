"""Thread management endpoints with orchestrated service."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_agent_service, get_thread_service
from app.schemas.thread import (
    ThreadListResponse,
    ThreadResponse,
    ThreadWithMessagesResponse,
)
from app.services.agent import AgentService
from app.services.threads import ThreadService

router = APIRouter()


@router.get("/user/{user_id}", response_model=ThreadListResponse)
async def get_all_threads_by_user(
    user_id: str,
    *,
    thread_service: ThreadService = Depends(get_thread_service),
) -> ThreadListResponse:
    """Get all threads for a specific user."""
    try:
        threads = await thread_service.aget_threads(user_id=user_id)
        return ThreadListResponse(
            threads=[ThreadResponse.model_validate(thread) for thread in threads]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{thread_id}/history", response_model=ThreadWithMessagesResponse)
async def get_thread_history(
    thread_id: str,
    *,
    thread_service: ThreadService = Depends(get_thread_service),
    agent_service: AgentService = Depends(get_agent_service),
) -> ThreadWithMessagesResponse:
    """Get thread history using RAG-enhanced retrieval."""
    try:
        # Get thread info first
        thread = await thread_service.aget_thread(thread_id, None)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Get messages using the orchestrator for enhanced retrieval
        messages = await agent_service.aget_history_chat(thread_id)

        # Combine thread info with messages
        thread_data = {
            "id": thread.id,
            "user_id": thread.user_id,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at,
            "deleted_at": thread.deleted_at,
            "messages": messages,
        }

        return ThreadWithMessagesResponse.model_validate(thread_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
