"""Dependency injection for API endpoints."""

from functools import lru_cache
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.orchestrator import ChatOrchestrator
from app.services.rag import RAGService
from app.services.users import UserService
from app.utils.database import get_db


@lru_cache
def get_rag_service() -> RAGService:
    """Get RAG service instance."""
    return RAGService()


def get_rag_service_optional() -> Optional[RAGService]:
    """Get RAG service instance, returns None if not available."""
    try:
        return get_rag_service()
    except Exception:
        return None


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service instance."""
    return UserService(session)


def get_chat_orchestrator(
    session: AsyncSession = Depends(get_db),
) -> ChatOrchestrator:
    """Get chat orchestrator instance."""
    rag_service = get_rag_service_optional()
    return ChatOrchestrator(session, rag_service)


# Legacy compatibility aliases
def get_unified_chat_service(
    session: AsyncSession = Depends(get_db),
) -> ChatOrchestrator:
    """Legacy alias for chat orchestrator."""
    return get_chat_orchestrator(session)


# ThreadService is still needed for thread management operations
def get_thread_service(session: AsyncSession = Depends(get_db)):
    """Get thread service instance."""
    from app.services.threads import ThreadService

    return ThreadService(session)
