"""
Authentication log database operations.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.database import BaseRepository


class AuthLogRepository(BaseRepository):
    """Repository for authentication log database operations."""

    async def create_auth_log(
        self,
        user_id: Optional[int],
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[asyncpg.Record]:
        """Create a new authentication log entry."""
        query = """
            INSERT INTO auth_logs (
                user_id, event_type, ip_address, user_agent, success, details
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, user_id, event_type, ip_address, user_agent, success, details, created_at
        """
        return await self.fetch_one(
            query,
            user_id,
            event_type,
            ip_address,
            user_agent,
            success,
            details,
        )

    async def get_auth_logs_by_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[asyncpg.Record]:
        """Get authentication logs for a specific user."""
        query = """
            SELECT id, user_id, event_type, ip_address, user_agent, success, details, created_at
            FROM auth_logs
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        return await self.fetch_many(query, user_id, limit, offset)

    async def get_auth_logs_by_event_type(
        self, event_type: str, limit: int = 100, offset: int = 0
    ) -> List[asyncpg.Record]:
        """Get authentication logs by event type."""
        query = """
            SELECT id, user_id, event_type, ip_address, user_agent, success, details, created_at
            FROM auth_logs
            WHERE event_type = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        return await self.fetch_many(query, event_type, limit, offset)

    async def get_failed_auth_logs(
        self, limit: int = 100, offset: int = 0
    ) -> List[asyncpg.Record]:
        """Get failed authentication attempts."""
        query = """
            SELECT id, user_id, event_type, ip_address, user_agent, success, details, created_at
            FROM auth_logs
            WHERE success = FALSE
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        return await self.fetch_many(query, limit, offset)

    async def get_auth_logs_by_ip(
        self, ip_address: str, limit: int = 100, offset: int = 0
    ) -> List[asyncpg.Record]:
        """Get authentication logs by IP address."""
        query = """
            SELECT id, user_id, event_type, ip_address, user_agent, success, details, created_at
            FROM auth_logs
            WHERE ip_address = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        return await self.fetch_many(query, ip_address, limit, offset)

    async def count_auth_logs_by_user(self, user_id: int) -> int:
        """Count authentication logs for a user."""
        query = """
            SELECT COUNT(*) FROM auth_logs WHERE user_id = $1
        """
        result = await self.fetch_one(query, user_id)
        return result["count"] if result else 0

    async def count_failed_attempts(
        self,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        hours: int = 24,
    ) -> int:
        """Count failed authentication attempts in the last N hours."""
        # Validate hours is a positive integer to prevent injection
        if not isinstance(hours, int) or hours < 1:
            hours = 24

        # Use PostgreSQL's make_interval function for safe parameterization
        if user_id:
            query = """
                SELECT COUNT(*) FROM auth_logs
                WHERE user_id = $1 AND success = FALSE 
                AND created_at > NOW() - make_interval(hours => $2)
            """
            result = await self.fetch_one(query, user_id, hours)
        elif ip_address:
            query = """
                SELECT COUNT(*) FROM auth_logs
                WHERE ip_address = $1 AND success = FALSE 
                AND created_at > NOW() - make_interval(hours => $2)
            """
            result = await self.fetch_one(query, ip_address, hours)
        else:
            query = """
                SELECT COUNT(*) FROM auth_logs
                WHERE success = FALSE 
                AND created_at > NOW() - make_interval(hours => $1)
            """
            result = await self.fetch_one(query, hours)
        return result["count"] if result else 0
