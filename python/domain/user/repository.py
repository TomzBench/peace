"""User repository - data access layer for user domain."""

import logging
from dataclasses import dataclass
from datetime import datetime
from textwrap import dedent
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from python.domain.user.models import User

logger = logging.getLogger(__name__)


@dataclass
class UserListFilter:
    """Pagination and filtering options for listing users."""

    skip: int = 0
    limit: int = 100
    active_only: bool = False


async def create_user(
    session: AsyncSession,
    user_data: dict[str, Any],
) -> User:
    """Create a new user.

    Args:
        session: Database session
        user_data: Dictionary of user fields

    Returns:
        Created user
    """
    logger.debug(
        dedent(f"""
            Repository: Creating user
            - email: {user_data.get('email')}
            - username: {user_data.get('username')}
        """).strip()
    )
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.debug(f"Repository: User created with ID={user.id}")
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Get user by ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        User if found, None otherwise
    """
    logger.debug(f"Repository: Querying user by ID={user_id}")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    logger.debug(f"Repository: User {'found' if user else 'not found'} for ID={user_id}")
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Get user by email.

    Args:
        session: Database session
        email: User email

    Returns:
        User if found, None otherwise
    """
    logger.debug(f"Repository: Querying user by email={email}")
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    logger.debug(f"Repository: User {'found' if user else 'not found'} for email={email}")
    return user


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Get user by username.

    Args:
        session: Database session
        username: Username

    Returns:
        User if found, None otherwise
    """
    logger.debug(f"Repository: Querying user by username={username}")
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    logger.debug(f"Repository: User {'found' if user else 'not found'} for username={username}")
    return user


async def list_users(
    session: AsyncSession,
    filters: UserListFilter | None = None,
) -> list[User]:
    """List users with pagination and filtering.

    Args:
        session: Database session
        filters: Pagination and filtering options

    Returns:
        List of users
    """
    filters = filters or UserListFilter()
    logger.debug(
        dedent(f"""
            Repository: Listing users
            - skip: {filters.skip}
            - limit: {filters.limit}
            - active_only: {filters.active_only}
        """).strip()
    )
    query = select(User)

    if filters.active_only:
        query = query.where(User.is_active == True)  # noqa: E712

    query = query.offset(filters.skip).limit(filters.limit)
    result = await session.execute(query)
    users = list(result.scalars().all())
    logger.debug(f"Repository: Found {len(users)} users")
    return users


async def update_user(
    session: AsyncSession,
    user: User,
    update_data: dict[str, Any],
) -> User:
    """Update user fields.

    Args:
        session: Database session
        user: User to update
        update_data: Dictionary of fields to update

    Returns:
        Updated user
    """
    logger.debug(f"Repository: Updating user ID={user.id}")

    # Update fields from dictionary
    for key, value in update_data.items():
        setattr(user, key, value)

    user.updated_at = datetime.utcnow()

    session.add(user)
    await session.commit()
    await session.refresh(user)

    fields_str = ", ".join(update_data.keys()) if update_data else "none"
    logger.debug(f"Repository: User ID={user.id} updated - fields: {fields_str}")
    return user


async def delete_user(session: AsyncSession, user: User) -> None:
    """Delete a user.

    Args:
        session: Database session
        user: User to delete
    """
    logger.debug(f"Repository: Deleting user ID={user.id}")
    await session.delete(user)
    await session.commit()
    logger.debug(f"Repository: User ID={user.id} deleted")


async def soft_delete_user(session: AsyncSession, user: User) -> User:
    """Soft delete a user by marking as inactive.

    Args:
        session: Database session
        user: User to soft delete

    Returns:
        Updated user
    """
    logger.debug(f"Repository: Soft deleting user ID={user.id}")
    result = await update_user(session, user, {"is_active": False})
    logger.debug(f"Repository: User ID={user.id} soft deleted")
    return result
