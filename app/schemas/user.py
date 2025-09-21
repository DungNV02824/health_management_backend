"""
User-related Pydantic schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.base import BaseSchema, TimestampMixin, IDMixin


class UserBase(BaseSchema):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")
    first_name: str = Field(
        ..., min_length=1, max_length=50, description="User first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=50, description="User last name"
    )
    is_active: bool = Field(
        default=True, description="Whether the user account is active"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        ..., min_length=8, max_length=128, description="User password"
    )


class UserUpdate(BaseSchema):
    """Schema for updating user information."""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class UserResponse(UserBase, IDMixin, TimestampMixin):
    """Schema for user response."""

    pass


class UserInDB(UserResponse):
    """Schema for user data stored in database."""

    password_hash: str = Field(..., description="Hashed password")


class UserLogin(BaseSchema):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseSchema):
    """Schema for authentication token."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    """Schema for token data."""

    email: Optional[str] = None
