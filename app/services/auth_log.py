"""
Authentication logging service.
"""

import asyncpg
from typing import Optional, Dict, Any
from fastapi import Request
from app.db.auth_log import AuthLogRepository
from app.constants import AuthEventType


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP address from request."""
    # Check for forwarded IP (when behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


class AuthLogService:
    """Service for logging authentication events."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.auth_log_repo = AuthLogRepository(db_pool)

    async def log_auth_event(
        self,
        event_type: AuthEventType,
        request: Request,
        user_id: Optional[int] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an authentication event."""
        try:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)

            await self.auth_log_repo.create_auth_log(
                user_id=user_id,
                event_type=event_type.value,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                details=details,
            )
        except Exception as e:
            # Don't let logging failures break the authentication flow
            # Log error but don't raise
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to log auth event: {e}")

    async def log_login_success(
        self, request: Request, user_id: int, provider: Optional[str] = None
    ) -> None:
        """Log successful login."""
        details = {"provider": provider} if provider else None
        await self.log_auth_event(
            AuthEventType.LOGIN_SUCCESS,
            request,
            user_id=user_id,
            success=True,
            details=details,
        )

    async def log_login_failed(
        self,
        request: Request,
        email: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log failed login attempt."""
        details = {}
        if email:
            details["email"] = email
        if reason:
            details["reason"] = reason
        await self.log_auth_event(
            AuthEventType.LOGIN_FAILED,
            request,
            user_id=None,
            success=False,
            details=details if details else None,
        )

    async def log_logout(self, request: Request, user_id: int) -> None:
        """Log logout event."""
        await self.log_auth_event(
            AuthEventType.LOGOUT,
            request,
            user_id=user_id,
            success=True,
        )

    async def log_logout_all(self, request: Request, user_id: int) -> None:
        """Log logout from all devices."""
        await self.log_auth_event(
            AuthEventType.LOGOUT_ALL,
            request,
            user_id=user_id,
            success=True,
        )

    async def log_email_verification_requested(
        self, request: Request, user_id: int
    ) -> None:
        """Log email verification request."""
        await self.log_auth_event(
            AuthEventType.EMAIL_VERIFICATION_REQUESTED,
            request,
            user_id=user_id,
            success=True,
        )

    async def log_email_verified(self, request: Request, user_id: int) -> None:
        """Log successful email verification."""
        await self.log_auth_event(
            AuthEventType.EMAIL_VERIFIED,
            request,
            user_id=user_id,
            success=True,
        )

    async def log_email_verification_failed(
        self, request: Request, reason: Optional[str] = None
    ) -> None:
        """Log failed email verification."""
        details = {"reason": reason} if reason else None
        await self.log_auth_event(
            AuthEventType.EMAIL_VERIFICATION_FAILED,
            request,
            user_id=None,
            success=False,
            details=details,
        )

    async def log_password_reset_requested(
        self, request: Request, email: Optional[str] = None
    ) -> None:
        """Log password reset request."""
        details = {"email": email} if email else None
        await self.log_auth_event(
            AuthEventType.PASSWORD_RESET_REQUESTED,
            request,
            user_id=None,
            success=True,
            details=details,
        )

    async def log_password_reset_success(self, request: Request, user_id: int) -> None:
        """Log successful password reset."""
        await self.log_auth_event(
            AuthEventType.PASSWORD_RESET_SUCCESS,
            request,
            user_id=user_id,
            success=True,
        )

    async def log_password_reset_failed(
        self, request: Request, reason: Optional[str] = None
    ) -> None:
        """Log failed password reset."""
        details = {"reason": reason} if reason else None
        await self.log_auth_event(
            AuthEventType.PASSWORD_RESET_FAILED,
            request,
            user_id=None,
            success=False,
            details=details,
        )

    async def log_password_changed(self, request: Request, user_id: int) -> None:
        """Log password change."""
        await self.log_auth_event(
            AuthEventType.PASSWORD_CHANGED,
            request,
            user_id=user_id,
            success=True,
        )

    async def log_oauth_login_success(
        self, request: Request, user_id: int, provider: str
    ) -> None:
        """Log successful OAuth login."""
        await self.log_auth_event(
            AuthEventType.OAUTH_LOGIN_SUCCESS,
            request,
            user_id=user_id,
            success=True,
            details={"provider": provider},
        )

    async def log_oauth_login_failed(
        self, request: Request, provider: str, reason: Optional[str] = None
    ) -> None:
        """Log failed OAuth login."""
        details = {"provider": provider}
        if reason:
            details["reason"] = reason
        await self.log_auth_event(
            AuthEventType.OAUTH_LOGIN_FAILED,
            request,
            user_id=None,
            success=False,
            details=details,
        )

    async def log_token_refresh_success(self, request: Request, user_id: int) -> None:
        """Log successful token refresh."""
        await self.log_auth_event(
            AuthEventType.TOKEN_REFRESH_SUCCESS,
            request,
            user_id=user_id,
            success=True,
        )

    async def log_token_refresh_failed(
        self, request: Request, reason: Optional[str] = None
    ) -> None:
        """Log failed token refresh."""
        details = {"reason": reason} if reason else None
        await self.log_auth_event(
            AuthEventType.TOKEN_REFRESH_FAILED,
            request,
            user_id=None,
            success=False,
            details=details,
        )

    async def log_token_revoked(self, request: Request, user_id: int) -> None:
        """Log token revocation."""
        await self.log_auth_event(
            AuthEventType.TOKEN_REVOKED,
            request,
            user_id=user_id,
            success=True,
        )
