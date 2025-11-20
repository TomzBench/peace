"""User CRUD routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from python.api.crud.user import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user,
)
from python.api.db import get_session
from python.api.models.user import User, UserCreate, UserRead, UserUpdate
from python.api.security import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

# Dependency injection type aliases
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/", response_model=UserRead, status_code=201)
async def create_user_endpoint(
    user_data: UserCreate,
    session: SessionDep,
) -> User:
    """Create a new user.

    Args:
        user_data: User creation data
        session: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If email already exists
    """
    logger.debug(f"POST /users/ - Creating user with email: {user_data.email}")

    # Check if email already exists
    existing_user = await get_user_by_email(session, user_data.email)
    if existing_user:
        logger.warning(f"User creation failed - email already registered: {user_data.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user with hashed password
    user = await create_user(
        session,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
    )

    logger.info(f"User created successfully - ID: {user.id}, email: {user.email}")
    return user


@router.get("/{user_id}", response_model=UserRead)
async def get_user_endpoint(
    user_id: int,
    session: SessionDep,
) -> User:
    """Get a user by ID.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        User data

    Raises:
        HTTPException: If user not found
    """
    logger.debug(f"GET /users/{user_id} - Fetching user")
    user = await get_user_by_id(session, user_id)
    if not user:
        logger.warning(f"User not found - ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    logger.debug(f"User retrieved successfully - ID: {user_id}, email: {user.email}")
    return user


@router.get("/", response_model=list[UserRead])
async def list_users_endpoint(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    active_only: bool = Query(False, description="Only return active users"),
) -> list[User]:
    """List users with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: Only return active users
        session: Database session

    Returns:
        List of users
    """
    logger.debug(
        f"GET /users/ - Listing users (skip={skip}, limit={limit}, active_only={active_only})"
    )
    users = await list_users(session, skip=skip, limit=limit, active_only=active_only)
    logger.info(
        f"Listed {len(users)} users (skip={skip}, limit={limit}, active_only={active_only})"
    )
    return users


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: int,
    user_data: UserUpdate,
    session: SessionDep,
) -> User:
    """Update a user.

    Args:
        user_id: User ID
        user_data: User update data
        session: Database session

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found
    """
    logger.debug(f"PATCH /users/{user_id} - Updating user")
    user = await get_user_by_id(session, user_id)
    if not user:
        logger.warning(f"User update failed - user not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    # Hash password if provided
    hashed_password = None
    if user_data.password:
        logger.debug(f"Hashing new password for user: {user_id}")
        hashed_password = hash_password(user_data.password)

    updated_user = await update_user(
        session,
        user,
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
    )

    logger.info(f"User updated successfully - ID: {user_id}, email: {updated_user.email}")
    return updated_user


@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: int,
    session: SessionDep,
) -> None:
    """Delete a user.

    Args:
        user_id: User ID
        session: Database session

    Raises:
        HTTPException: If user not found
    """
    logger.debug(f"DELETE /users/{user_id} - Deleting user")
    user = await get_user_by_id(session, user_id)
    if not user:
        logger.warning(f"User deletion failed - user not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    await delete_user(session, user)
    logger.info(f"User deleted successfully - ID: {user_id}")
