"""Tests for QDrant vector database functionality."""

import pytest
from qdrant_client import AsyncQdrantClient

from python.infra.db.vector import close_vector_db, get_vector_db, init_vector_db


def test_get_vector_db_returns_client() -> None:
    """Test that get_vector_db returns a QDrant client."""
    client = get_vector_db()
    assert isinstance(client, AsyncQdrantClient)
    assert client is not None


def test_get_vector_db_returns_same_instance() -> None:
    """Test that get_vector_db returns the same instance on multiple calls."""
    client1 = get_vector_db()
    client2 = get_vector_db()
    assert client1 is client2  # Should be the same object


@pytest.mark.asyncio
async def test_init_vector_db() -> None:
    """Test that init_vector_db doesn't raise an exception."""
    # This should not raise an exception
    await init_vector_db()

    # Verify client is initialized
    client = get_vector_db()
    assert client is not None


@pytest.mark.asyncio
async def test_close_vector_db() -> None:
    """Test that close_vector_db closes the connection."""
    # Get client first to ensure it's initialized
    get_vector_db()

    # Close should not raise an exception
    await close_vector_db()
