"""Tests for configuration loading."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from textwrap import dedent

import pytest
from pydantic import ValidationError

from python.config import Settings


def test_settings_load_without_yaml() -> None:
    """Test Settings.load() works when no YAML file exists."""
    # Use a non-existent file path
    settings = Settings.load(config_file="/nonexistent/config.yaml")

    # Should use defaults
    assert settings.app_name == "Peace API"
    assert settings.debug is False
    assert settings.log_level == "INFO"


def test_settings_load_with_yaml() -> None:
    """Test Settings.load() merges YAML configuration."""
    # Create a temporary YAML config file
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            dedent(
                """
                app_name: "Test App"
                debug: true
                log_level: "DEBUG"
                database_url: "postgresql://test:test@localhost/testdb"
                """
            ).strip()
        )
        config_path = f.name

    try:
        # Load settings from YAML
        settings = Settings.load(config_file=config_path)

        # Verify YAML values were loaded
        assert settings.app_name == "Test App"
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.database_url == "postgresql://test:test@localhost/testdb"

        # Verify defaults still work for unspecified values
        assert settings.echo_sql is False
        assert settings.api_v1_prefix == "/api/v1"
    finally:
        # Clean up temp file
        Path(config_path).unlink()


def test_settings_load_env_vars_override_yaml() -> None:
    """Test that environment variables override YAML config."""
    # Create a temporary YAML config file
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            dedent(
                """
                app_name: "YAML App"
                debug: false
                """
            ).strip()
        )
        config_path = f.name

    try:
        # Set environment variable
        os.environ["APP_NAME"] = "ENV App"
        os.environ["DEBUG"] = "true"

        # Load settings from YAML
        settings = Settings.load(config_file=config_path)

        # Environment variables should override YAML
        assert settings.app_name == "ENV App"
        assert settings.debug is True
    finally:
        # Clean up
        Path(config_path).unlink()
        os.environ.pop("APP_NAME", None)
        os.environ.pop("DEBUG", None)


def test_settings_load_uses_env_var_for_config_path() -> None:
    """Test that PEACE_CONFIG_FILE environment variable is used."""
    # Create a temporary YAML config file
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            dedent(
                """
                app_name: "Config from ENV path"
                """
            ).strip()
        )
        config_path = f.name

    try:
        # Set PEACE_CONFIG_FILE environment variable
        os.environ["PEACE_CONFIG_FILE"] = config_path

        # Load settings without specifying config_file
        settings = Settings.load()

        # Should load from the path specified in env var
        assert settings.app_name == "Config from ENV path"
    finally:
        # Clean up
        Path(config_path).unlink()
        os.environ.pop("PEACE_CONFIG_FILE", None)


def test_settings_load_explicit_path_overrides_env_var() -> None:
    """Test that explicit config_file parameter overrides PEACE_CONFIG_FILE."""
    # Create two temporary YAML config files
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f1:
        f1.write('app_name: "Config 1"\n')
        config_path1 = f1.name

    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f2:
        f2.write('app_name: "Config 2"\n')
        config_path2 = f2.name

    try:
        # Set PEACE_CONFIG_FILE to config1
        os.environ["PEACE_CONFIG_FILE"] = config_path1

        # But explicitly load config2
        settings = Settings.load(config_file=config_path2)

        # Should use the explicit path (config2)
        assert settings.app_name == "Config 2"
    finally:
        # Clean up
        Path(config_path1).unlink()
        Path(config_path2).unlink()
        os.environ.pop("PEACE_CONFIG_FILE", None)


def test_settings_validation_error_invalid_type() -> None:
    """Test that Pydantic raises ValidationError for invalid config values."""
    # Create a temporary YAML config file with invalid types
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            dedent(
                """
                app_name: "Test App"
                debug: "not-a-boolean"  # Invalid: should be boolean
                echo_sql: 12345  # Invalid: should be boolean
                """
            ).strip()
        )
        config_path = f.name

    try:
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            Settings.load(config_file=config_path)

        # Verify error contains details about the invalid fields
        error = exc_info.value
        assert "debug" in str(error)
        assert "echo_sql" in str(error)
    finally:
        # Clean up temp file
        Path(config_path).unlink()
