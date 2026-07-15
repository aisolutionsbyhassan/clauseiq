"""
ClauseIQ — Application Configuration

All environment-driven configuration is centralized here via Pydantic Settings.
No configuration values should be hardcoded in service code — reference this
settings object instead.
"""

import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Defaults are provided for development convenience but should be
    overridden in production via environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "ClauseIQ"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://clauseiq_user:clauseiq_pass@localhost:5432/clauseiq_db"

    # --- JWT Authentication ---
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # --- Groq AI ---
    GROQ_API_KEY: str = ""

    # --- ChromaDB ---
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"
    CHROMA_COLLECTION_NAME: str = "clauseiq_chunks"

    # --- File Upload ---
    MAX_UPLOAD_SIZE_MB: int = 25
    UPLOAD_DIRECTORY: str = "./storage"

    # --- Document Processing ---
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 50

    # --- RAG / Retrieval ---
    RETRIEVAL_TOP_K: int = 5

    # --- Embedding Model ---
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # --- Dashboard ---
    DASHBOARD_RECENT_UPLOADS_LIMIT: int = 5

    # --- CORS ---
    CORS_ORIGINS: str = '["http://localhost:5173"]'

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS JSON string into a list."""
        return json.loads(self.CORS_ORIGINS)

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB limit to bytes for file validation."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def database_url_sync(self) -> str:
        """Return a synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")


settings = Settings()
