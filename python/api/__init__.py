"""FastAPI application package."""

from python.api.asgi import app
from python.api.main import create_app

__all__ = ["app", "create_app"]
