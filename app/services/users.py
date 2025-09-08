"""User service for user-related operations."""

from typing import Literal, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.models.user import User
from app.schemas.user import UserCreateRequest


class UserService:
    """Simplified service for user operations - direct database access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, request: UserCreateRequest) -> User:
        """Create a new user."""
        try:
            user = User(name=request.name, withdrawed_amount=0.0)
            self.session.add(user)
            await self.session.commit()
            return user
        except Exception as e:
            raise DatabaseError(f"Failed to create user: {e}")

    async def get_user_profile(self, user_id: str) -> Optional[User]:
        """Get user profile by ID."""
        try:
            stmt = (
                select(User).where(User.id == user_id).where(User.deleted_at.is_(None))
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Failed to get user profile: {e}")

    async def classify_user_profile(
        self, user_id: Optional[str]
    ) -> Literal["newbie", "average", "good"]:
        """Classify user profile based on data."""
        if not user_id:
            return "newbie"

        user = await self.get_user_profile(user_id)
        if not user:
            return "newbie"

        # Simple classification logic based on withdrawn amount
        if user.withdrawed_amount == 0:
            return "newbie"
        elif user.withdrawed_amount < 5000:
            return "average"
        else:
            return "good"
