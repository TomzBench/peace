"""QDrant vector database setup with dual database support - functional approach."""

import logging
from typing import Literal

from qdrant_client import AsyncQdrantClient

from python.api.config import settings

logger = logging.getLogger(__name__)

# Type alias for database selection
DatabaseType = Literal["db1", "db2"]

# Module-level database clients (initialized on first import)
_db1_client: AsyncQdrantClient | None = None
_db2_client: AsyncQdrantClient | None = None


def _get_or_create_db1() -> AsyncQdrantClient:
    """Get or create the first QDrant database client."""
    global _db1_client
    if _db1_client is None:
        logger.info(f"Creating QDrant db1 client with URL: {settings.qdrant_url_1}")
        _db1_client = AsyncQdrantClient(
            url=settings.qdrant_url_1,
            api_key=settings.qdrant_api_key,
        )
        logger.debug("QDrant db1 client created successfully")
    else:
        logger.debug("Reusing existing QDrant db1 client")
    return _db1_client


def _get_or_create_db2() -> AsyncQdrantClient:
    """Get or create the second QDrant database client."""
    global _db2_client
    if _db2_client is None:
        logger.info(f"Creating QDrant db2 client with URL: {settings.qdrant_url_2}")
        _db2_client = AsyncQdrantClient(
            url=settings.qdrant_url_2,
            api_key=settings.qdrant_api_key,
        )
        logger.debug("QDrant db2 client created successfully")
    else:
        logger.debug("Reusing existing QDrant db2 client")
    return _db2_client


def get_vector_db(db_type: DatabaseType = "db1") -> AsyncQdrantClient:
    """Get a QDrant database client.

    Args:
        db_type: Which database to use ("db1" or "db2")

    Returns:
        QDrant async client instance
    """
    logger.debug(f"Requesting vector database: {db_type}")
    if db_type == "db1":
        return _get_or_create_db1()
    return _get_or_create_db2()


async def close_vector_dbs() -> None:
    """Close all vector database connections."""
    global _db1_client, _db2_client

    logger.info("Closing vector database connections")
    if _db1_client is not None:
        logger.debug("Closing QDrant db1 client")
        await _db1_client.close()
        _db1_client = None
        logger.debug("QDrant db1 client closed")

    if _db2_client is not None:
        logger.debug("Closing QDrant db2 client")
        await _db2_client.close()
        _db2_client = None
        logger.debug("QDrant db2 client closed")

    logger.info("All vector database connections closed")


async def init_vector_dbs() -> None:
    """Initialize vector database clients.

    This is optional - clients are created lazily on first access.
    Call this explicitly if you want to ensure connections at startup.
    """
    logger.info("Initializing vector database clients")
    _get_or_create_db1()
    _get_or_create_db2()
    logger.info("Vector database clients initialized")
