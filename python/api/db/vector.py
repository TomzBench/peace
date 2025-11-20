"""QDrant vector database setup with dual database support - functional approach."""

from typing import Literal

from qdrant_client import AsyncQdrantClient

from python.api.config import settings

# Type alias for database selection
DatabaseType = Literal["db1", "db2"]

# Module-level database clients (initialized on first import)
_db1_client: AsyncQdrantClient | None = None
_db2_client: AsyncQdrantClient | None = None


def _get_or_create_db1() -> AsyncQdrantClient:
    """Get or create the first QDrant database client."""
    global _db1_client
    if _db1_client is None:
        _db1_client = AsyncQdrantClient(
            url=settings.qdrant_url_1,
            api_key=settings.qdrant_api_key,
        )
    return _db1_client


def _get_or_create_db2() -> AsyncQdrantClient:
    """Get or create the second QDrant database client."""
    global _db2_client
    if _db2_client is None:
        _db2_client = AsyncQdrantClient(
            url=settings.qdrant_url_2,
            api_key=settings.qdrant_api_key,
        )
    return _db2_client


def get_vector_db(db_type: DatabaseType = "db1") -> AsyncQdrantClient:
    """Get a QDrant database client.

    Args:
        db_type: Which database to use ("db1" or "db2")

    Returns:
        QDrant async client instance
    """
    if db_type == "db1":
        return _get_or_create_db1()
    return _get_or_create_db2()


async def close_vector_dbs() -> None:
    """Close all vector database connections."""
    global _db1_client, _db2_client

    if _db1_client is not None:
        await _db1_client.close()
        _db1_client = None

    if _db2_client is not None:
        await _db2_client.close()
        _db2_client = None


async def init_vector_dbs() -> None:
    """Initialize vector database clients.

    This is optional - clients are created lazily on first access.
    Call this explicitly if you want to ensure connections at startup.
    """
    _get_or_create_db1()
    _get_or_create_db2()
