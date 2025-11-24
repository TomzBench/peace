"""Application configuration using Pydantic settings."""

import logging
import os
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationError
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from ruamel.yaml import YAML


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Custom settings source that loads configuration from YAML files."""

    def __init__(self, settings_cls: type[BaseSettings], config_file: str | None = None):
        """Initialize the YAML settings source."""
        super().__init__(settings_cls)
        self.config_file = config_file or os.environ.get("PEACE_CONFIG_FILE", "config.yaml")
        self.yaml_data: dict[str, Any] = {}
        self._load_yaml()

    def _load_yaml(self) -> None:
        """Load YAML configuration file."""
        config_path = Path(self.config_file)
        if config_path.exists():
            logging.debug(f"Loading configuration from {config_path}")
            yaml = YAML(typ="safe")
            with config_path.open() as f:
                self.yaml_data = yaml.load(f) or {}
            logging.debug(f"Loaded {len(self.yaml_data)} settings from YAML")
        else:
            logging.debug(f"Config file {config_path} not found")

    def get_field_value(
        self, field_info: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        """Get field value from YAML data."""
        field_value = self.yaml_data.get(field_name)
        return field_value, field_name, False

    def __call__(self) -> dict[str, Any]:
        """Return the YAML configuration data."""
        return self.yaml_data


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

    # Logging
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite+aiosqlite:///./peace.db"
    echo_sql: bool = False
    downloads_dir: Path = Path(".downloads")

    # QDrant Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # OpenAI API (for Whisper transcription)
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_organization: str | None = Field(default=None, validation_alias="OPENAI_ORGANIZATION")

    # API
    api_v1_prefix: str = "/api/v1"

    # Internal field to store config file path
    _config_file: str | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize the settings sources and their priority."""
        # Get config file path from class attribute or use default
        config_file = getattr(cls, "_config_file", None)

        # Return sources in priority order (first = highest priority)
        return (
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls, config_file),
            init_settings,
        )

    @classmethod
    def load(cls, config_file: str | None = None) -> "Settings":
        """Load settings from YAML file with environment variable overrides.

        Raises ValidationError.
        """
        # Determine the actual config file path being used
        actual_config_file = config_file or os.environ.get("PEACE_CONFIG_FILE", "config.yaml")

        # Store config file path in class attribute for settings_customise_sources
        cls._config_file = config_file
        try:
            # Create Settings instance - Pydantic will use our custom sources
            return cls()
        except ValidationError as e:
            # Add context about which config file caused the error
            logging.error(f"Configuration validation failed for: {actual_config_file}")
            logging.error(f"Error details:\n{e}")
            raise
        finally:
            # Clean up class attribute
            cls._config_file = None


# Context variable for clean access (optional/cache layer)
_settings_context: ContextVar[Settings | None] = ContextVar("settings", default=None)


def get_settings() -> Settings:
    """Get the current settings."""
    settings = _settings_context.get()
    if settings is None:
        # Fallback to loading from YAML (for backwards compatibility or CLI usage)
        settings = Settings.load()
        _settings_context.set(settings)
    return settings


def set_settings(settings: Settings) -> None:
    """Set settings in context (called by app factory)."""
    _settings_context.set(settings)
    configure_logging(settings)


def configure_logging(settings: Settings) -> None:
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,  # Force reconfiguration even if already configured
    )
