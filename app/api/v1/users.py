"""User management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import aget_asyncpg_session
from app.core.exceptions import WeAssistantException
from app.schemas.user import UserCreateRequest, UserResponse
from app.services.users import UserService

router = APIRouter()


def get_user_service(
    session: AsyncSession = Depends(aget_asyncpg_session),
) -> UserService:
    """Get user service instance."""
    return UserService(session)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    request: UserCreateRequest,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""
    try:
        user = await user_service.create_user(request)
        return UserResponse.model_validate(user)
    except WeAssistantException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
