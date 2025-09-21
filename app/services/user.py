"""
User business logic and services.
"""

import asyncpg
from typing import Optional, List
from datetime import timedelta
from app.db.user import UserRepository
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    UserLogin,
    Token,
)
from app.utils import hash_password, verify_password, create_access_token
from app.config import settings


class UserService:
    """Service layer for user operations."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.user_repo = UserRepository(db_pool)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.user_repo.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        user_record = await self.user_repo.create_user(user_data, password_hash)
        if not user_record:
            raise RuntimeError("Failed to create user")

        return UserResponse(**dict(user_record))

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID."""
        user_record = await self.user_repo.get_user_by_id(user_id)
        if not user_record:
            return None

        return UserResponse(**dict(user_record))

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email (includes password hash for authentication)."""
        user_record = await self.user_repo.get_user_by_email(email)
        if not user_record:
            return None

        return UserInDB(**dict(user_record))

    async def get_users(self, limit: int = 100, offset: int = 0) -> List[UserResponse]:
        """Get all users with pagination."""
        user_records = await self.user_repo.get_users(limit, offset)
        return [UserResponse(**dict(record)) for record in user_records]

    async def update_user(
        self, user_id: int, user_data: UserUpdate
    ) -> Optional[UserResponse]:
        """Update user information."""
        # Check if user exists
        existing_user = await self.user_repo.get_user_by_id(user_id)
        if not existing_user:
            return None

        # Check if email is being changed and if it's already taken
        if user_data.email and user_data.email != existing_user["email"]:
            email_user = await self.user_repo.get_user_by_email(user_data.email)
            if email_user:
                raise ValueError("Email is already taken")

        # Update user
        user_record = await self.user_repo.update_user(user_id, user_data)
        if not user_record:
            return None

        return UserResponse(**dict(user_record))

    async def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete)."""
        result = await self.user_repo.delete_user(user_id)
        return result is not None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user by email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        return user

    async def login_user(self, login_data: UserLogin) -> Token:
        """Login user and return access token."""
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise ValueError("Invalid email or password")

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        return Token(access_token=access_token)

    async def count_users(self) -> int:
        """Count total users."""
        return await self.user_repo.count_users()
