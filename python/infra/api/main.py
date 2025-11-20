"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from python.config import Settings, set_settings
from python.infra.api.routes import app as app_routes
from python.infra.api.routes import users
from python.infra.db import shutdown_db, startup_db


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    """Application factory function.

    Args:
        custom_settings: Optional custom settings. If None, loads from YAML config.

    Returns:
        Configured FastAPI application

    Examples:
        # Default settings from YAML config + environment
        app = create_app()

        # Custom settings
        settings = Settings(database_url="postgresql://...")
        app = create_app(settings)
    """
    # Initialize settings
    app_settings = custom_settings or Settings.load()

    # Set in ContextVar for clean access throughout the app
    set_settings(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage application lifecycle - startup and shutdown events."""
        # Store settings in app.state (FastAPI native way)
        app.state.settings = app_settings

        # Also ensure ContextVar is set (for background tasks, etc.)
        set_settings(app_settings)

        # Startup
        await startup_db()
        yield
        # Shutdown
        await shutdown_db()

    # Create FastAPI application
    app = FastAPI(
        title=app_settings.app_name,
        debug=app_settings.debug,
        lifespan=lifespan,
    )

    # Store settings in app.state for FastAPI patterns
    app.state.settings = app_settings

    # Include routers
    app.include_router(app_routes.router)
    app.include_router(users.router)

    return app
