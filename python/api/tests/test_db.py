"""Tests for SQL database infrastructure."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


@pytest.mark.asyncio
async def test_session_creation(test_session: AsyncSession) -> None:
    """Test that a database session can be created."""
    assert test_session is not None
    assert isinstance(test_session, AsyncSession)


@pytest.mark.asyncio
async def test_database_transaction(test_session: AsyncSession) -> None:
    """Test basic database transaction operations."""
    result = await test_session.execute(select(1))
    value = result.scalar_one()
    assert value == 1


@pytest.mark.asyncio
async def test_session_rollback(test_session: AsyncSession) -> None:
    """Test that session rollback works."""
    await test_session.rollback()
    # Session should still be usable after rollback
    result = await test_session.execute(select(1))
    value = result.scalar_one()
    assert value == 1


@pytest.mark.asyncio
async def test_session_commit(test_session: AsyncSession) -> None:
    """Test that session commit works."""
    # Execute a query
    result = await test_session.execute(select(1))
    value = result.scalar_one()
    assert value == 1

    # Commit should not raise an error
    await test_session.commit()


@pytest.mark.asyncio
async def test_multiple_queries_in_session(test_session: AsyncSession) -> None:
    """Test that multiple queries can be executed in one session."""
    result1 = await test_session.execute(select(1))
    value1 = result1.scalar_one()

    result2 = await test_session.execute(select(2))
    value2 = result2.scalar_one()

    assert value1 == 1
    assert value2 == 2
