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
        self, user_data: UserCreate, password_hash: Optional[str] = None
    ) -> Optional[asyncpg.Record]:
        """Create a new user."""
        now = datetime.utcnow()
        query = """
            INSERT INTO users (
                email, first_name, last_name, password_hash, is_active, 
                provider, google_id, avatar_url, email_verified, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
            RETURNING id, email, first_name, last_name, is_active, provider, 
                      google_id, avatar_url, email_verified, created_at, updated_at
        """
        return await self.fetch_one(
            query,
            user_data.email,
            user_data.first_name,
            user_data.last_name,
            password_hash,
            user_data.is_active,
            user_data.provider,
            user_data.google_id,
            user_data.avatar_url,
            user_data.email_verified,
            now,
        )

    async def get_user_by_id(self, user_id: int) -> Optional[asyncpg.Record]:
        """Get user by ID."""
        query = """
            SELECT id, email, first_name, last_name, password_hash, is_active, provider,
                   google_id, avatar_url, email_verified, email_verification_token,
                   email_verification_sent_at, password_reset_token, password_reset_sent_at,
                   created_at, updated_at
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
        """
        return await self.fetch_one(query, user_id)

    async def get_user_by_email(self, email: str) -> Optional[asyncpg.Record]:
        """Get user by email."""
        query = """
            SELECT id, email, first_name, last_name, password_hash, is_active, provider,
                   google_id, avatar_url, email_verified, email_verification_token,
                   email_verification_sent_at, password_reset_token, password_reset_sent_at,
                   created_at, updated_at
            FROM users
            WHERE email = $1 AND deleted_at IS NULL
        """
        return await self.fetch_one(query, email)

    async def get_users(
        self, limit: int = 100, offset: int = 0
    ) -> List[asyncpg.Record]:
        """Get all users with pagination."""
        query = """
            SELECT id, email, first_name, last_name, is_active, provider,
                   avatar_url, email_verified, created_at, updated_at
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

    # OAuth and Authentication methods

    async def get_user_by_google_id(self, google_id: str) -> Optional[asyncpg.Record]:
        """Get user by Google ID."""
        query = """
            SELECT id, email, first_name, last_name, password_hash, is_active, provider,
                   google_id, avatar_url, email_verified, created_at, updated_at
            FROM users
            WHERE google_id = $1 AND deleted_at IS NULL
        """
        return await self.fetch_one(query, google_id)

    async def set_email_verification_token(self, user_id: int, token: str) -> bool:
        """Set email verification token for user."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET email_verification_token = $2,
                email_verification_sent_at = $3,
                updated_at = $3
            WHERE id = $1 AND deleted_at IS NULL
        """
        result = await self.execute(query, user_id, token, now)
        return "UPDATE 1" in result

    async def verify_email(self, token: str) -> Optional[asyncpg.Record]:
        """Verify email using token."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET email_verified = TRUE,
                email_verification_token = NULL,
                email_verification_sent_at = NULL,
                updated_at = $2
            WHERE email_verification_token = $1 AND deleted_at IS NULL
            RETURNING id, email, first_name, last_name
        """
        return await self.fetch_one(query, token, now)

    async def set_password_reset_token(self, email: str, token: str) -> bool:
        """Set password reset token for user."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET password_reset_token = $2,
                password_reset_sent_at = $3,
                updated_at = $3
            WHERE email = $1 AND deleted_at IS NULL
        """
        result = await self.execute(query, email, token, now)
        return "UPDATE 1" in result

    async def reset_password(
        self, token: str, password_hash: str
    ) -> Optional[asyncpg.Record]:
        """Reset password using token."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET password_hash = $2,
                password_reset_token = NULL,
                password_reset_sent_at = NULL,
                updated_at = $3
            WHERE password_reset_token = $1 AND deleted_at IS NULL
            RETURNING id, email, first_name, last_name
        """
        return await self.fetch_one(query, token, password_hash, now)

    async def update_password(self, user_id: int, password_hash: str) -> bool:
        """Update user password."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET password_hash = $2, updated_at = $3
            WHERE id = $1 AND deleted_at IS NULL
        """
        result = await self.execute(query, user_id, password_hash, now)
        return "UPDATE 1" in result

    async def link_google_account(
        self, user_id: int, google_id: str, avatar_url: Optional[str] = None
    ) -> bool:
        """Link Google account to existing user."""
        now = datetime.utcnow()
        query = """
            UPDATE users
            SET google_id = $2, avatar_url = COALESCE($3, avatar_url), updated_at = $4
            WHERE id = $1 AND deleted_at IS NULL
        """
        result = await self.execute(query, user_id, google_id, avatar_url, now)
        return "UPDATE 1" in result

    # Refresh Token methods

    async def store_refresh_token(
        self, user_id: int, token_hash: str, expires_at: datetime
    ) -> Optional[asyncpg.Record]:
        """Store a refresh token in the database."""
        query = """
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, token_hash, expires_at, revoked, created_at, updated_at
        """
        return await self.fetch_one(query, user_id, token_hash, expires_at)

    async def get_refresh_token_by_hash(
        self, token_hash: str
    ) -> Optional[asyncpg.Record]:
        """Get a refresh token by its hash."""
        query = """
            SELECT id, user_id, token_hash, expires_at, revoked, created_at, updated_at
            FROM refresh_tokens
            WHERE token_hash = $1 AND revoked = FALSE
        """
        return await self.fetch_one(query, token_hash)

    async def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token by marking it as revoked."""
        now = datetime.utcnow()
        query = """
            UPDATE refresh_tokens
            SET revoked = TRUE, updated_at = $2
            WHERE token_hash = $1 AND revoked = FALSE
        """
        result = await self.execute(query, token_hash, now)
        return "UPDATE 1" in result or "UPDATE 0" in result

    async def revoke_all_user_refresh_tokens(self, user_id: int) -> bool:
        """Revoke all refresh tokens for a user."""
        now = datetime.utcnow()
        query = """
            UPDATE refresh_tokens
            SET revoked = TRUE, updated_at = $2
            WHERE user_id = $1 AND revoked = FALSE
        """
        result = await self.execute(query, user_id, now)
        return True  # Always return True, even if no tokens were revoked

    async def cleanup_expired_refresh_tokens(self) -> int:
        """Delete expired refresh tokens from the database."""
        query = """
            DELETE FROM refresh_tokens
            WHERE expires_at < NOW()
        """
        result = await self.execute(query)
        # Extract number from result string like "DELETE 5"
        try:
            return int(result.split()[-1]) if result.split()[-1].isdigit() else 0
        except (IndexError, ValueError):
            return 0
