"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from python.api.config import settings
from python.api.db import shutdown_db, startup_db
from python.api.routes import users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle - startup and shutdown events."""
    # Startup
    await startup_db()
    yield
    # Shutdown
    await shutdown_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# Include routers
app.include_router(users.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health check."""
    return {"status": "ok", "message": f"Welcome to {settings.app_name}"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
