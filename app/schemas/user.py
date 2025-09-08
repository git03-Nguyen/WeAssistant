"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    """Request schema for creating a new user."""

    name: str = Field(..., min_length=1, max_length=100, description="User name")

    class Config:
        json_schema_extra = {"example": {"name": "John Doe"}}


class UserResponse(BaseModel):
    """User response schema."""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    withdrawed_amount: float = Field(..., description="Total withdrawn amount")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")
    deleted_at: Optional[datetime] = Field(
        None, description="Deletion date if soft deleted"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "user-123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "withdrawed_amount": 1500.0,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "deleted_at": None,
            }
        }


class UserProfileClassification(BaseModel):
    """User profile classification result."""

    classification: Literal["newbie", "average", "good"] = Field(
        ..., description="User classification based on profile"
    )

    class Config:
        json_schema_extra = {"example": {"classification": "average"}}
