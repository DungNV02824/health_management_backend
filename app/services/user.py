"""
User business logic and services.
"""

import asyncpg
from typing import Optional, List
from datetime import timedelta, datetime, timezone
from app.constants import UserProviders
from app.db.user import UserRepository
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    UserLogin,
    Token,
    TokenPair,
    PasswordResetRequest,
    PasswordReset,
    EmailVerification,
    GoogleOAuthCallback,
)
from app.helpers import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_refresh_token,
    create_verification_token,
    verify_verification_token,
)
from app.config import settings
from app.services.email import email_service


class UserService:
    """Service layer for user operations."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.user_repo = UserRepository(db_pool)

    async def create_user(
        self, user_data: UserCreate, send_verification: bool = True
    ) -> UserResponse:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.user_repo.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # For OAuth users, check if Google ID already exists
        if user_data.google_id:
            existing_google_user = await self.user_repo.get_user_by_google_id(
                user_data.google_id
            )
            if existing_google_user:
                raise ValueError("User with this Google account already exists")

        # Hash password if provided (not required for OAuth users)
        password_hash = None
        if user_data.password:
            password_hash = hash_password(user_data.password)
        elif user_data.provider == UserProviders.PORTAL:
            raise ValueError("Password is required for portal accounts")

        # Create user
        user_record = await self.user_repo.create_user(user_data, password_hash)
        if not user_record:
            raise RuntimeError("Failed to create user")

        # Send email verification for portal accounts (OAuth users are pre-verified)
        if (
            send_verification
            and user_data.provider == UserProviders.PORTAL
            and not user_data.email_verified
        ):
            await self._send_email_verification(
                user_record["id"], user_data.email, user_data.first_name
            )

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

    # Enhanced Authentication Methods

    async def _send_email_verification(
        self, user_id: int, email: str, first_name: str
    ) -> bool:
        """Send email verification token to user."""
        # Generate verification token
        verification_token = create_verification_token(email, "email_verification")

        # Store token in database
        await self.user_repo.set_email_verification_token(user_id, verification_token)
        base_url = settings.webui_url
        # Send verification email
        return await email_service.send_email_verification(
            email, first_name, verification_token, base_url
        )

    async def verify_email(self, verification_data: EmailVerification) -> bool:
        """Verify user email with token."""
        # Verify token and get email
        email = verify_verification_token(verification_data.token, "email_verification")
        if not email:
            raise ValueError("Invalid or expired verification token")

        # Update user in database
        result = await self.user_repo.verify_email(verification_data.token)
        return result is not None

    async def request_password_reset(self, reset_request: PasswordResetRequest) -> bool:
        """Request password reset for user."""
        # Check if user exists
        user = await self.user_repo.get_user_by_email(reset_request.email)
        if not user:
            # Don't reveal if email exists or not
            return True

        # Generate reset token
        reset_token = create_verification_token(reset_request.email, "password_reset")

        # Store token in database
        await self.user_repo.set_password_reset_token(reset_request.email, reset_token)

        # Send reset email
        return await email_service.send_password_reset(
            reset_request.email, user["first_name"], reset_token
        )

    async def reset_password(self, reset_data: PasswordReset) -> bool:
        """Reset user password with token."""
        # Verify token and get email
        email = verify_verification_token(reset_data.token, "password_reset")
        if not email:
            raise ValueError("Invalid or expired reset token")

        # Hash new password
        password_hash = hash_password(reset_data.new_password)

        # Update password in database
        result = await self.user_repo.reset_password(reset_data.token, password_hash)
        return result is not None

    async def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password (requires old password verification)."""
        # Get current user
        user = await self.get_user_by_email_with_password(user_id)
        if not user or not user.password_hash:
            raise ValueError("User not found or has no password")

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise ValueError("Invalid current password")

        # Hash new password
        password_hash = hash_password(new_password)

        # Update password
        return await self.user_repo.update_password(user_id, password_hash)

    async def get_user_by_email_with_password(self, user_id: int) -> Optional[UserInDB]:
        """Get user with password hash (for password verification)."""
        user_record = await self.user_repo.get_user_by_id(user_id)
        if not user_record:
            return None
        return UserInDB(**dict(user_record))

    # OAuth Methods

    async def create_oauth_user(self, oauth_data: GoogleOAuthCallback) -> UserResponse:
        """Create user from OAuth data."""
        print(oauth_data)
        user_data = UserCreate(
            email=oauth_data.email,
            first_name=oauth_data.given_name or "User",
            last_name=oauth_data.family_name or "Unknown",
            provider="google",
            google_id=oauth_data.id,
            avatar_url=oauth_data.picture,
            email_verified=oauth_data.email_verified,
        )

        return await self.create_user(user_data, send_verification=False)

    async def authenticate_oauth_user(
        self, oauth_data: GoogleOAuthCallback
    ) -> UserInDB:
        """Authenticate user with OAuth data."""
        # Try to find user by Google ID first
        user_record = await self.user_repo.get_user_by_google_id(oauth_data.id)

        if user_record:
            return UserInDB(**dict(user_record))

        # Try to find user by email
        user_record = await self.user_repo.get_user_by_email(oauth_data.email)

        if user_record:
            # Link Google account to existing user
            await self.user_repo.link_google_account(
                user_record["id"], oauth_data.id, oauth_data.picture
            )
            # Get updated user record
            user_record = await self.user_repo.get_user_by_id(user_record["id"])
            return UserInDB(**dict(user_record))

        # Create new user
        user_response = await self.create_oauth_user(oauth_data)
        user_record = await self.user_repo.get_user_by_id(user_response.id)
        return UserInDB(**dict(user_record))

    async def login_with_oauth(self, oauth_data: GoogleOAuthCallback) -> TokenPair:
        """Login user with OAuth and return token pair."""
        user = await self.authenticate_oauth_user(oauth_data)

        if not user.is_active:
            raise ValueError("User account is disabled")

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        # Create refresh token
        refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=refresh_token_expires,
        )

        # Store refresh token in database
        token_hash = hash_refresh_token(refresh_token)
        expires_at = datetime.utcnow() + refresh_token_expires
        await self.user_repo.store_refresh_token(user.id, token_hash, expires_at)

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    # Enhanced login with refresh token support
    async def login_with_refresh_token(self, login_data: UserLogin) -> TokenPair:
        """Login user and return access and refresh tokens."""
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise ValueError("Invalid email or password")

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        # Create refresh token
        refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=refresh_token_expires,
        )

        # Store refresh token in database
        token_hash = hash_refresh_token(refresh_token)
        expires_at = datetime.utcnow() + refresh_token_expires
        await self.user_repo.store_refresh_token(user.id, token_hash, expires_at)

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Refresh access token using a refresh token."""
        # Verify refresh token JWT
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise ValueError("Invalid refresh token")

        # Check if token exists in database and is valid
        token_hash = hash_refresh_token(refresh_token)
        token_record = await self.user_repo.get_refresh_token_by_hash(token_hash)

        if not token_record:
            raise ValueError("Refresh token not found or already revoked")

        # Check if token is expired (handle timezone-aware comparison)
        expires_at = token_record["expires_at"]
        if isinstance(expires_at, datetime) and expires_at.tzinfo is not None:
            # Database returns timezone-aware datetime
            if datetime.now(timezone.utc) > expires_at:
                raise ValueError("Refresh token has expired")
        else:
            # Fallback for timezone-naive datetime
            if datetime.utcnow() > expires_at:
                raise ValueError("Refresh token has expired")

        # Get user
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Invalid token payload")

        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Revoke old refresh token
        await self.user_repo.revoke_refresh_token(token_hash)

        # Create new access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        # Create new refresh token (token rotation)
        refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
        new_refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=refresh_token_expires,
        )

        # Store new refresh token in database
        new_token_hash = hash_refresh_token(new_refresh_token)
        expires_at = datetime.utcnow() + refresh_token_expires
        await self.user_repo.store_refresh_token(user.id, new_token_hash, expires_at)

        return TokenPair(access_token=access_token, refresh_token=new_refresh_token)

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""
        token_hash = hash_refresh_token(refresh_token)
        return await self.user_repo.revoke_refresh_token(token_hash)

    async def logout_user(self, user_id: int) -> bool:
        """Logout user by revoking all refresh tokens."""
        return await self.user_repo.revoke_all_user_refresh_tokens(user_id)
