"""Functional CRUD operations for User model."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from python.api.models.user import User


async def create_user(
    session: AsyncSession,
    email: str,
    username: str,
    hashed_password: str,
    full_name: str | None = None,
) -> User:
    """Create a new user.

    Args:
        session: Database session
        email: User email
        username: Username
        hashed_password: Already hashed password
        full_name: Optional full name

    Returns:
        Created user
    """
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Get user by ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        User if found, None otherwise
    """
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Get user by email.

    Args:
        session: Database session
        email: User email

    Returns:
        User if found, None otherwise
    """
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Get user by username.

    Args:
        session: Database session
        username: Username

    Returns:
        User if found, None otherwise
    """
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def list_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[User]:
    """List users with pagination.

    Args:
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: Only return active users

    Returns:
        List of users
    """
    query = select(User)

    if active_only:
        query = query.where(User.is_active == True)  # noqa: E712

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession,
    user: User,
    email: str | None = None,
    username: str | None = None,
    full_name: str | None = None,
    hashed_password: str | None = None,
    is_active: bool | None = None,
) -> User:
    """Update user fields.

    Args:
        session: Database session
        user: User to update
        email: New email (optional)
        username: New username (optional)
        full_name: New full name (optional)
        hashed_password: New hashed password (optional)
        is_active: New active status (optional)

    Returns:
        Updated user
    """
    if email is not None:
        user.email = email
    if username is not None:
        user.username = username
    if full_name is not None:
        user.full_name = full_name
    if hashed_password is not None:
        user.hashed_password = hashed_password
    if is_active is not None:
        user.is_active = is_active

    user.updated_at = datetime.utcnow()

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user: User) -> None:
    """Delete a user.

    Args:
        session: Database session
        user: User to delete
    """
    await session.delete(user)
    await session.commit()


async def soft_delete_user(session: AsyncSession, user: User) -> User:
    """Soft delete a user by marking as inactive.

    Args:
        session: Database session
        user: User to soft delete

    Returns:
        Updated user
    """
    return await update_user(session, user, is_active=False)
