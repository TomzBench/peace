"""Tests for User model and schema."""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from python.domain.user.models import User, UserCreate, UserRead, UserUpdate

# Unit Tests - Model instantiation and validation


def test_user_model_instantiation() -> None:
    """Test that User model can be instantiated."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw",
    )

    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.hashed_password == "hashed_pw"
    assert user.is_active is True  # Default value
    assert user.id is None  # Not persisted yet


def test_user_model_defaults() -> None:
    """Test that User model has correct default values."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw",
    )

    assert user.is_active is True
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_model_with_optional_fields() -> None:
    """Test User model with optional fields."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw",
        full_name="Test User",
        is_active=False,
    )

    assert user.full_name == "Test User"
    assert user.is_active is False


def test_user_create_schema() -> None:
    """Test UserCreate schema validation."""
    user_create = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Test User",
    )

    assert user_create.email == "test@example.com"
    assert user_create.username == "testuser"
    assert user_create.password == "password123"
    assert user_create.full_name == "Test User"


def test_user_create_schema_without_full_name() -> None:
    """Test UserCreate schema with optional full_name omitted."""
    user_create = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )

    assert user_create.full_name is None


def test_user_update_schema() -> None:
    """Test UserUpdate schema with optional fields."""
    user_update = UserUpdate(email="newemail@example.com")

    assert user_update.email == "newemail@example.com"
    assert user_update.username is None
    assert user_update.full_name is None


def test_user_update_schema_all_fields() -> None:
    """Test UserUpdate schema with all fields."""
    user_update = UserUpdate(
        email="newemail@example.com",
        username="newusername",
        full_name="New Name",
        password="newpassword123",
    )

    assert user_update.email == "newemail@example.com"
    assert user_update.username == "newusername"
    assert user_update.full_name == "New Name"
    assert user_update.password == "newpassword123"


def test_user_read_schema() -> None:
    """Test UserRead schema (no password field)."""
    user_read = UserRead(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
    )

    assert user_read.id == 1
    assert user_read.email == "test@example.com"
    # UserRead should not have password field
    assert not hasattr(user_read, "password")
    assert not hasattr(user_read, "hashed_password")


# Integration Tests - Database operations


@pytest.mark.asyncio
async def test_user_table_created(test_session: AsyncSession) -> None:
    """Test that User table is created in database."""
    # Try to insert a user to verify table exists
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw",
    )
    test_session.add(user)
    await test_session.commit()

    # Verify it was inserted
    result = await test_session.execute(select(User))
    users = result.scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_user_persisted_with_id(test_session: AsyncSession) -> None:
    """Test that User gets an ID when persisted."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw",
    )
    assert user.id is None

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, int)


@pytest.mark.asyncio
async def test_user_unique_email_constraint(test_session: AsyncSession) -> None:
    """Test that email uniqueness is enforced."""
    user1 = User(
        email="test@example.com",
        username="user1",
        hashed_password="hash1",
    )
    test_session.add(user1)
    await test_session.commit()

    # Try to create another user with same email
    user2 = User(
        email="test@example.com",  # Duplicate!
        username="user2",
        hashed_password="hash2",
    )
    test_session.add(user2)

    with pytest.raises(IntegrityError):
        await test_session.commit()


@pytest.mark.asyncio
async def test_user_unique_username_constraint(test_session: AsyncSession) -> None:
    """Test that username uniqueness is enforced."""
    user1 = User(
        email="user1@example.com",
        username="testuser",
        hashed_password="hash1",
    )
    test_session.add(user1)
    await test_session.commit()

    # Try to create another user with same username
    user2 = User(
        email="user2@example.com",
        username="testuser",  # Duplicate!
        hashed_password="hash2",
    )
    test_session.add(user2)

    with pytest.raises(IntegrityError):
        await test_session.commit()


@pytest.mark.asyncio
async def test_user_timestamps_on_create(test_session: AsyncSession) -> None:
    """Test that timestamps are set correctly on creation."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_pw",
    )

    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)

    assert user.created_at is not None
    assert user.updated_at is not None
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)
