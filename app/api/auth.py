"""
Enhanced Authentication API endpoints.
"""

from typing import Annotated
import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from app.services.user import UserService
from app.services.oauth import google_oauth_service
from app.db.database import get_database_pool
from app.auth.dependencies import get_current_active_user
from app.schemas.user import (
    UserInDB,
    TokenPair,
    RefreshToken,
    PasswordResetRequest,
    PasswordReset,
    EmailVerification,
    GoogleOAuthRequest,
    UserLogin,
)

router = APIRouter()


async def get_user_service(
    db_pool: asyncpg.Pool = Depends(get_database_pool),
) -> UserService:
    """Dependency to get user service."""
    return UserService(db_pool)


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    verification_data: EmailVerification,
    user_service: UserService = Depends(get_user_service),
):
    """Verify user email with verification token."""
    try:
        success = await user_service.verify_email(verification_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification failed",
            )
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )


@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email_from_link(
    token: str = Query(..., description="Email verification token"),
    user_service: UserService = Depends(get_user_service),
):
    """Verify user email from email link (GET endpoint for email links)."""
    try:
        verification_data = EmailVerification(token=token)
        success = await user_service.verify_email(verification_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email verification failed",
            )
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_email_verification(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    user_service: UserService = Depends(get_user_service),
):
    """Resend email verification for current user."""
    try:
        if current_user.email_verified:
            return {"message": "Email is already verified"}

        await user_service._send_email_verification(
            current_user.id, current_user.email, current_user.first_name
        )
        return {"message": "Verification email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )


@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    user_service: UserService = Depends(get_user_service),
):
    """Request password reset email."""
    try:
        await user_service.request_password_reset(reset_request)
        # Always return success to avoid email enumeration
        return {"message": "If the email exists, a password reset link has been sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed",
        )


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: PasswordReset,
    user_service: UserService = Depends(get_user_service),
):
    """Reset password with token."""
    try:
        success = await user_service.reset_password(reset_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed",
            )
        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    old_password: str,
    new_password: str,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    user_service: UserService = Depends(get_user_service),
):
    """Change password for authenticated user."""
    try:
        success = await user_service.change_password(
            current_user.id, old_password, new_password
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed",
            )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


# Google OAuth Endpoints


@router.get("/google/login")
async def google_login(
    redirect_url: str = Query(
        default="http://localhost:8000/auth/callback",
        description="Frontend callback URL",
    ),
):
    """Initiate Google OAuth login."""
    try:
        if not google_oauth_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google OAuth is not configured",
            )

        authorization_url, state = google_oauth_service.get_authorization_url()

        # In a real application, you might want to store the state and redirect_url
        # in Redis or database for security validation

        return {
            "authorization_url": authorization_url,
            "state": state,
            "redirect_url": redirect_url,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google OAuth",
        )


@router.post("/google/callback", response_model=TokenPair)
async def google_callback(
    oauth_request: GoogleOAuthRequest,
    user_service: UserService = Depends(get_user_service),
):
    """Handle Google OAuth callback and authenticate user."""
    try:
        if not google_oauth_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google OAuth is not configured",
            )

        # Verify OAuth code and get user info
        oauth_data = await google_oauth_service.verify_oauth_token(
            oauth_request.code, oauth_request.state
        )

        if not oauth_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth authorization code",
            )

        # Authenticate user and get tokens
        tokens = await user_service.login_with_oauth(oauth_data)
        return tokens

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        print(f"OAuth authentication failed {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed {e}",
        )


@router.get("/google/callback")
async def google_callback_redirect(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(None, description="OAuth state parameter"),
    error: str = Query(None, description="OAuth error"),
    request: Request = None,
):
    """Handle Google OAuth callback redirect (for direct browser redirects)."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}",
        )

    # This endpoint can redirect to frontend with the code
    # Frontend then calls the POST callback endpoint
    frontend_url = "http://localhost:3000/auth/callback"  # This should be configurable
    return RedirectResponse(
        url=f"{frontend_url}?code={code}&state={state}",
        status_code=status.HTTP_302_FOUND,
    )


# Enhanced login with refresh token
@router.post("/login-with-refresh", response_model=TokenPair)
async def login_with_refresh_token(
    login_data: UserLogin,
    user_service: UserService = Depends(get_user_service),
):
    """Login user and return access and refresh tokens."""
    try:
        tokens = await user_service.login_with_refresh_token(login_data)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to login"
        )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    refresh_token_data: RefreshToken,
    user_service: UserService = Depends(get_user_service),
):
    """Refresh access token using a refresh token."""
    try:
        tokens = await user_service.refresh_access_token(
            refresh_token_data.refresh_token
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token",
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    refresh_token_data: RefreshToken,
    user_service: UserService = Depends(get_user_service),
):
    """Logout user by revoking a refresh token."""
    try:
        success = await user_service.revoke_refresh_token(
            refresh_token_data.refresh_token
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to revoke token",
            )
        return {"message": "Logged out successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    user_service: UserService = Depends(get_user_service),
):
    """Logout user from all devices by revoking all refresh tokens."""
    try:
        success = await user_service.logout_user(current_user.id)
        return {"message": "Logged out from all devices successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )


@router.get("/me", response_model=UserInDB)
async def get_current_user_info(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    """Get current authenticated user information."""
    return current_user
