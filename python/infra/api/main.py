"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from python.config import Settings, set_settings
from python.infra.api.routes import agent, users
from python.infra.api.routes import app as app_routes
from python.infra.api.routes.exceptions import register_exception_handlers

# from python.infra.api.routes import audio, users
from python.infra.db import shutdown_db, startup_db


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    """Application factory function."""
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

    # Add CORS middleware for browser extension support
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins (browser extensions)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store settings in app.state for FastAPI patterns
    app.state.settings = app_settings

    # Include routers
    app.include_router(app_routes.router)
    app.include_router(users.router)
    app.include_router(agent.router)
    register_exception_handlers(app)

    return app
