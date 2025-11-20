"""QDrant vector database setup - functional approach.

This module provides a single QDrant client for storing vector embeddings.
Planned use: Store video audio transcriptions and embeddings.
"""

import logging

from qdrant_client import AsyncQdrantClient

from python.config import get_settings

logger = logging.getLogger(__name__)

# Module-level database client (initialized lazily)
_client: AsyncQdrantClient | None = None


def get_vector_db() -> AsyncQdrantClient:
    """Get the QDrant database client.

    Client is created lazily on first access and reused for subsequent calls.

    Returns:
        QDrant async client instance
    """
    global _client
    if _client is None:
        settings = get_settings()
        logger.info(f"Creating QDrant client with URL: {settings.qdrant_url}")
        _client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        logger.debug("QDrant client created successfully")
    else:
        logger.debug("Reusing existing QDrant client")
    return _client


async def close_vector_db() -> None:
    """Close the vector database connection."""
    global _client

    if _client is not None:
        logger.info("Closing QDrant client")
        await _client.close()
        _client = None
        logger.debug("QDrant client closed")
    else:
        logger.debug("No QDrant client to close")


async def init_vector_db() -> None:
    """Initialize vector database client.

    This is optional - client is created lazily on first access.
    Call this explicitly if you want to ensure connection at startup.
    """
    logger.info("Initializing vector database client")
    get_vector_db()
    logger.info("Vector database client initialized")
