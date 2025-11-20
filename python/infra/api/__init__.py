"""FastAPI application package."""

from python.infra.api.asgi import app
from python.infra.api.main import create_app

__all__ = ["app", "create_app"]
