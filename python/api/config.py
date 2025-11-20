"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Peace API"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./peace.db"
    echo_sql: bool = False

    # QDrant Vector Databases
    qdrant_url_1: str = "http://localhost:6333"
    qdrant_url_2: str = "http://localhost:6334"
    qdrant_api_key: str | None = None

    # API
    api_v1_prefix: str = "/api/v1"


# Global settings instance
settings = Settings()
