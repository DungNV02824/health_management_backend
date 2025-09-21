"""
Configuration settings for the Health Management application.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    app_name: str = "Health Management API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database settings
    database_url: str = Field(..., description="PostgreSQL database URL")
    database_pool_min_size: int = 1
    database_pool_max_size: int = 20
    database_pool_timeout: float = 30.0

    # Security settings
    secret_key: str = Field(..., description="Secret key for JWT token signing")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API settings
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: list[str] = ["*"]

    # CORS settings
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
