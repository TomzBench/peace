"""CLI entry point for running the Peace API with configuration options."""

import argparse
import logging
import sys
from textwrap import dedent

import uvicorn

from python.api.config import Settings, configure_logging
from python.api.main import create_app

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Peace API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            Examples:
              # Run with default config (config.yaml or env vars)
              python -m python.api

              # Run with custom config file
              python -m python.api --config /path/to/config.yaml

              # Run with custom config and port
              python -m python.api --config prod.yaml --port 8080

              # Run in development mode with auto-reload
              python -m python.api --reload

            Environment Variables:
              PEACE_CONFIG_FILE    Path to YAML config file (overridden by --config)
              APP_NAME            Application name
              DEBUG               Debug mode (true/false)
              LOG_LEVEL           Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
              DATABASE_URL        Database connection URL
              QDRANT_URL          QDrant vector database URL
              QDRANT_API_KEY      QDrant API key (optional)
            """
        ).strip(),
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to YAML configuration file (overrides PEACE_CONFIG_FILE env var)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Uvicorn log level (overrides config file setting)",
    )

    return parser.parse_args()


def main() -> None:
    """Main CLI entry point."""
    args = parse_args()

    # Load settings from config file
    try:
        settings = Settings.load(config_file=args.config)
    except Exception as e:
        # Print to stderr before logging is configured
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Configure logging infrastructure
    configure_logging(settings)

    # Log startup information
    logger.info(f"Starting {settings.app_name}")
    if args.config:
        logger.info(f"Using config file: {args.config}")
    logger.info(f"Server will start at: http://{args.host}:{args.port}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Debug mode: {settings.debug}")

    # Create the FastAPI app with loaded settings
    app = create_app(custom_settings=settings)

    # Determine uvicorn log level (CLI arg > config setting)
    uvicorn_log_level = args.log_level or settings.log_level.lower()

    # Run uvicorn server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # Can't use workers with reload
        log_level=uvicorn_log_level,
    )


if __name__ == "__main__":
    main()
