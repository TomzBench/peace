"""Application health and info routes."""

from fastapi import APIRouter

from python.api.dependencies import SettingsDepClean

router = APIRouter(tags=["app"])


@router.get("/")
async def root(settings: SettingsDepClean) -> dict[str, str]:
    """Root endpoint for health check."""
    return {"status": "ok", "message": f"Welcome to {settings.app_name}"}


@router.get("/health")
async def health(settings: SettingsDepClean) -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@router.get("/info")
async def get_app_info(settings: SettingsDepClean) -> dict[str, str]:
    """Get app info - demonstrates clean settings access without injection."""
    return {
        "app_name": settings.app_name,
        "debug": str(settings.debug),
        "log_level": settings.log_level,
        "database_url": settings.database_url.split("://")[0] + "://***",  # Hide credentials
    }
