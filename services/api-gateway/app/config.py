"""
Application configuration using pydantic-settings.

Loads settings from environment variables with sensible defaults
for local development.
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tetraploid_snpmap"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Computation micro-service
    COMPUTATION_SERVICE_URL: str = "http://localhost:8001"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 100

    # Security
    SECRET_KEY: str = "change-me-in-production"

    # Storage
    PROJECT_STORAGE_PATH: str = "/tmp/tetraploid_snpmap/projects"

    # Application metadata
    APP_TITLE: str = "TetraploidSNPMap API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "REST API for TetraploidSNPMap -- a genetic linkage mapping tool "
        "for autotetraploid organisms.  Supports SNP, SNP-QTL and non-SNP "
        "(RFLP/AFLP/SSR) analysis modes."
    )

    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
