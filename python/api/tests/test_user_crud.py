"""Tests for user CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from python.api.crud.user import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    list_users,
    soft_delete_user,
    update_user,
)
from python.api.models.user import User


@pytest.mark.asyncio
async def test_create_user(test_session: AsyncSession) -> None:
    """Test creating a user."""
    user = await create_user(
        test_session,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password_here",
        full_name="Test User",
    )

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_get_user_by_id(test_session: AsyncSession) -> None:
    """Test getting a user by ID."""
    # Create a user
    created_user = await create_user(
        test_session,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
    )

    assert created_user.id is not None

    # Get the user
    user = await get_user_by_id(test_session, created_user.id)

    assert user is not None
    assert user.id == created_user.id
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(test_session: AsyncSession) -> None:
    """Test getting a non-existent user by ID."""
    user = await get_user_by_id(test_session, 99999)
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email(test_session: AsyncSession) -> None:
    """Test getting a user by email."""
    await create_user(
        test_session,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
    )

    user = await get_user_by_email(test_session, "test@example.com")

    assert user is not None
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_username(test_session: AsyncSession) -> None:
    """Test getting a user by username."""
    await create_user(
        test_session,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
    )

    user = await get_user_by_username(test_session, "testuser")

    assert user is not None
    assert user.username == "testuser"


@pytest.mark.asyncio
async def test_list_users(test_session: AsyncSession) -> None:
    """Test listing users."""
    # Create multiple users
    await create_user(
        test_session,
        email="user1@example.com",
        username="user1",
        hashed_password="hash1",
    )
    await create_user(
        test_session,
        email="user2@example.com",
        username="user2",
        hashed_password="hash2",
    )
    await create_user(
        test_session,
        email="user3@example.com",
        username="user3",
        hashed_password="hash3",
    )

    users = await list_users(test_session)

    assert len(users) == 3
    assert all(isinstance(u, User) for u in users)


@pytest.mark.asyncio
async def test_list_users_pagination(test_session: AsyncSession) -> None:
    """Test listing users with pagination."""
    # Create multiple users
    for i in range(5):
        await create_user(
            test_session,
            email=f"user{i}@example.com",
            username=f"user{i}",
            hashed_password=f"hash{i}",
        )

    # Get first 2 users
    users_page1 = await list_users(test_session, skip=0, limit=2)
    assert len(users_page1) == 2

    # Get next 2 users
    users_page2 = await list_users(test_session, skip=2, limit=2)
    assert len(users_page2) == 2

    # Ensure different users
    assert users_page1[0].id != users_page2[0].id


@pytest.mark.asyncio
async def test_list_users_active_only(test_session: AsyncSession) -> None:
    """Test listing only active users."""
    # Create active user
    active_user = await create_user(
        test_session,
        email="active@example.com",
        username="active",
        hashed_password="hash",
    )

    # Create inactive user
    inactive_user = await create_user(
        test_session,
        email="inactive@example.com",
        username="inactive",
        hashed_password="hash",
    )
    await update_user(test_session, inactive_user, is_active=False)

    # List only active users
    users = await list_users(test_session, active_only=True)

    assert len(users) == 1
    assert users[0].id == active_user.id


@pytest.mark.asyncio
async def test_update_user(test_session: AsyncSession) -> None:
    """Test updating a user."""
    user = await create_user(
        test_session,
        email="test@example.com",
        username="testuser",
        hashed_password="hash",
    )

    updated_user = await update_user(
        test_session,
        user,
        email="newemail@example.com",
        full_name="New Name",
    )

    assert updated_user.email == "newemail@example.com"
    assert updated_user.full_name == "New Name"
    assert updated_user.username == "testuser"  # Unchanged
    assert updated_user.updated_at > updated_user.created_at


@pytest.mark.asyncio
async def test_delete_user(test_session: AsyncSession) -> None:
    """Test deleting a user."""
    user = await create_user(
        test_session,
        email="test@example.com",
        username="testuser",
        hashed_password="hash",
    )

    assert user.id is not None
    user_id = user.id
    await delete_user(test_session, user)

    # Verify user is deleted
    deleted_user = await get_user_by_id(test_session, user_id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_soft_delete_user(test_session: AsyncSession) -> None:
    """Test soft deleting a user."""
    user = await create_user(
        test_session,
        email="test@example.com",
        username="testuser",
        hashed_password="hash",
    )

    assert user.id is not None
    await soft_delete_user(test_session, user)

    # User still exists but is inactive
    inactive_user = await get_user_by_id(test_session, user.id)
    assert inactive_user is not None
    assert inactive_user.is_active is False
