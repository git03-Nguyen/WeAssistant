"""User management endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_user_service
from app.schemas.user import UserCreateRequest, UserResponse
from app.services.users import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    request: UserCreateRequest,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""
    try:
        user = await user_service.acreate_user(request)
        return UserResponse.model_validate(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
