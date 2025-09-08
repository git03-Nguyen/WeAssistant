"""Thread management endpoints with orchestrated service."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_chat_orchestrator
from app.core.exceptions import WeAssistantException
from app.schemas.thread import ThreadListResponse, ThreadWithMessagesResponse
from app.services.orchestrator import ChatOrchestrator
from app.services.threads import ThreadService
from app.utils.database import get_db

router = APIRouter()


def get_thread_service(session: AsyncSession = Depends(get_db)) -> ThreadService:
    """Get thread service instance."""
    return ThreadService(session)


@router.get("/user/{user_id}", response_model=ThreadListResponse)
async def get_all_threads_by_user(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    thread_service: ThreadService = Depends(get_thread_service),
) -> ThreadListResponse:
    """Get all threads for a specific user."""
    try:
        threads, total = await thread_service.list_threads(
            user_id=user_id, page=page, size=size
        )

        from app.schemas.thread import ThreadResponse

        return ThreadListResponse(
            threads=[ThreadResponse.model_validate(thread) for thread in threads],
            total=total,
            page=page,
            size=size,
        )
    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{thread_id}/history", response_model=ThreadWithMessagesResponse)
async def get_thread_history(
    thread_id: str,
    limit: int = Query(None, ge=1, le=1000, description="Limit number of messages"),
    thread_service: ThreadService = Depends(get_thread_service),
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> ThreadWithMessagesResponse:
    """Get thread history using RAG-enhanced retrieval."""
    try:
        # Get thread info first
        thread = await thread_service.get_thread(thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Get messages using the orchestrator for enhanced retrieval
        messages = await orchestrator.get_thread_history(thread_id, limit)

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
    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
