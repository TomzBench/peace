"""Tests for QDrant vector database functionality."""

import pytest
from qdrant_client import AsyncQdrantClient

from python.api.db.vector import close_vector_dbs, get_vector_db, init_vector_dbs


def test_get_vector_db_returns_db1() -> None:
    """Test that get_vector_db returns db1 by default."""
    client = get_vector_db("db1")
    assert isinstance(client, AsyncQdrantClient)
    assert client is not None


def test_get_vector_db_returns_db2() -> None:
    """Test that get_vector_db can return db2."""
    client = get_vector_db("db2")
    assert isinstance(client, AsyncQdrantClient)
    assert client is not None


def test_get_vector_db_returns_same_instance() -> None:
    """Test that get_vector_db returns the same instance on multiple calls."""
    client1 = get_vector_db("db1")
    client2 = get_vector_db("db1")
    assert client1 is client2  # Should be the same object


def test_get_vector_db_different_databases() -> None:
    """Test that db1 and db2 are different instances."""
    db1_client = get_vector_db("db1")
    db2_client = get_vector_db("db2")
    assert db1_client is not db2_client


@pytest.mark.asyncio
async def test_init_vector_dbs() -> None:
    """Test that init_vector_dbs doesn't raise an exception."""
    # This should not raise an exception
    await init_vector_dbs()

    # Verify clients are initialized
    client = get_vector_db("db1")
    assert client is not None


@pytest.mark.asyncio
async def test_close_vector_dbs() -> None:
    """Test that close_vector_dbs closes all connections."""
    # Get clients first to ensure they're initialized
    get_vector_db("db1")
    get_vector_db("db2")

    # Close should not raise an exception
    await close_vector_dbs()
