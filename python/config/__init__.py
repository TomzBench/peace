"""Shared configuration module for Peace project.

This module provides configuration management with YAML support,
environment variable overrides, and Pydantic validation.
"""

from python.config.settings import (
    Settings,
    configure_logging,
    get_settings,
    set_settings,
)

__all__ = [
    "Settings",
    "configure_logging",
    "get_settings",
    "set_settings",
]
