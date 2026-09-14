"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the Hospital AI Assistant."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "PulsePoint CareOS"
    PROJECT_NAME: str = "PulsePoint CareOS"
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hospital_ai"

    JWT_SECRET_KEY: str = Field(..., min_length=16)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ADMIN_EMAIL: str = "admin@hospital.com"
    ADMIN_PASSWORD: str = "change-this-password"
    ADMIN_FULL_NAME: str = "System Administrator"

    FIRST_SUPERUSER_EMAIL: str = ""
    FIRST_SUPERUSER_PASSWORD: str = ""
    FIRST_SUPERUSER_FULL_NAME: str = ""

    UPLOAD_DIR: str = "data/storage"
    KNOWLEDGE_BASE_PATH: str = "data/knowledge_base"
    VECTOR_INDEX_PATH: str = "data/vector_index/index.faiss"
    VECTOR_METADATA_PATH: str = "data/vector_index/metadata.json"

    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_MAX_BYTES: int = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    RAG_TOP_K: int = 3
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_MIN_SCORE: float = 0.0

    LLM_PROVIDER: str = "retrieval_only"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    @property
    def effective_admin_email(self) -> str:
        """Resolve admin email from either ADMIN_EMAIL or FIRST_SUPERUSER_EMAIL."""
        if self.FIRST_SUPERUSER_EMAIL:
            return self.FIRST_SUPERUSER_EMAIL
        return self.ADMIN_EMAIL

    @property
    def effective_admin_password(self) -> str:
        """Resolve admin password from either ADMIN_PASSWORD or FIRST_SUPERUSER_PASSWORD."""
        if self.FIRST_SUPERUSER_PASSWORD:
            return self.FIRST_SUPERUSER_PASSWORD
        return self.ADMIN_PASSWORD

    @property
    def effective_admin_full_name(self) -> str:
        """Resolve admin name."""
        if self.FIRST_SUPERUSER_FULL_NAME:
            return self.FIRST_SUPERUSER_FULL_NAME
        return self.ADMIN_FULL_NAME

    @field_validator("RAG_TOP_K")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        """Ensure top-k is a positive retrieval size."""
        if value < 1:
            raise ValueError("RAG_TOP_K must be at least 1")
        return value

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        """Restrict LLM provider names."""
        allowed = {"groq", "retrieval_only"}
        normalized = value.lower().strip()
        if normalized not in allowed:
            raise ValueError(f"LLM_PROVIDER must be one of {allowed}")
        return normalized


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
