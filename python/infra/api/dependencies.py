"""Shared FastAPI dependencies.

All dependency injection type aliases are defined here for reuse across routes.
"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from python.config import Settings
from python.config import get_settings as get_settings_from_context
from python.infra.db.sql import get_session


def get_settings_from_request(request: Request) -> Settings:
    """Get settings from app.state (FastAPI native pattern)."""
    settings: Settings = request.app.state.settings
    return settings


def get_settings() -> Settings:
    """Get settings from context (hybrid pattern)."""
    return get_settings_from_context()


# Settings dependency type aliases (choose your style)
SettingsDepExplicit = Annotated[Settings, Depends(get_settings_from_request)]  # Requires Request
SettingsDepClean = Annotated[Settings, Depends(get_settings)]  # Uses ContextVar

# Database session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]
