"""
User database operations using raw SQL queries.
"""

import asyncpg
from typing import Optional, List
from datetime import datetime
from app.db.database import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository):
    """Repository for user database operations."""

    async def create_user(
        self, user_data: UserCreate, password_hash: str
    ) -> Optional[asyncpg.Record]:
        """Create a new user."""
        now = datetime.utcnow()
        query = """
            INSERT INTO users (email, first_name, last_name, password_hash, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $6)
            RETURNING id, email, first_name, last_name, is_active, created_at, updated_at
        """
        return await self.fetch_one(
            query,
            user_data.email,
            user_data.first_name,
            user_data.last_name,
            password_hash,
            user_data.is_active,
            now,
        )

    async def get_user_by_id(self, user_id: int) -> Optional[asyncpg.Record]:
        """Get user by ID."""
        query = """
            SELECT id, email, first_name, last_name, password_hash, is_active, created_at, updated_at
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
        """
        return await self.fetch_one(query, user_id)

    async def get_user_by_email(self, email: str) -> Optional[asyncpg.Record]:
        """Get user by email."""
        query = """
        SELECT id, email, first_name, last_name, password_hash, is_active, created_at, updated_at
        FROM users
        WHERE email = $1 AND deleted_at IS NULL
    """
        return await self.fetch_one(query, email)

    async def get_users(
        self, limit: int = 100, offset: int = 0
    ) -> List[asyncpg.Record]:
        """Get all users with pagination."""
        query = """
            SELECT id, email, first_name, last_name, is_active, created_at, updated_at
            FROM users
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        return await self.fetch_many(query, limit, offset)

    async def update_user(
        self, user_id: int, user_data: UserUpdate
    ) -> Optional[asyncpg.Record]:
        """Update user information."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET email = COALESCE($2, email),
                first_name = COALESCE($3, first_name),
                last_name = COALESCE($4, last_name),
                is_active = COALESCE($5, is_active),
                updated_at = $6
            WHERE id = $1 AND deleted_at IS NULL
            RETURNING id, email, first_name, last_name, is_active, created_at, updated_at
        """
        return await self.fetch_one(
            query,
            user_id,
            user_data.email,
            user_data.first_name,
            user_data.last_name,
            user_data.is_active,
            now,
        )

    async def delete_user(self, user_id: int) -> Optional[asyncpg.Record]:
        """Soft delete user."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET deleted_at = $2, updated_at = $2
            WHERE id = $1 AND deleted_at IS NULL
            RETURNING id
        """
        return await self.fetch_one(query, user_id, now)

    async def count_users(self) -> int:
        """Count total users."""
        query = """
            SELECT COUNT(*) FROM users WHERE deleted_at IS NULL
        """
        result = await self.fetch_one(query)
        return result["count"] if result else 0
