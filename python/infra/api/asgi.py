"""ASGI entry point for production servers.

This module creates the FastAPI application instance that ASGI servers
(uvicorn, gunicorn, hypercorn, etc.) use to run the application.

For CLI argument support (--config, --port, etc.), use python.api.cli instead.

Usage with ASGI servers (uses PEACE_CONFIG_FILE env var or config.yaml):
    uvicorn python.api.asgi:app --reload
    gunicorn python.api.asgi:app -w 4 -k uvicorn.workers.UvicornWorker
    PEACE_CONFIG_FILE=prod.yaml uvicorn python.api.asgi:app

Usage with CLI runner (supports --config argument):
    python -m python.api --config myconfig.yaml
    python -m python.api --config myconfig.yaml --port 8080 --reload
"""

from python.infra.api.main import create_app

# Create application instance
# Settings are loaded from YAML config file + environment variables
# Config file path: PEACE_CONFIG_FILE env var or "config.yaml" (default)
app = create_app()
