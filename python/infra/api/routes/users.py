"""User CRUD routes."""

import logging
from textwrap import dedent

from fastapi import APIRouter, HTTPException, Query

from python.domain.user.models import User, UserCreate, UserRead, UserUpdate
from python.domain.user.repository import (
    UserListFilter,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user,
)
from python.infra.api.dependencies import SessionDep
from python.infra.api.security import hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


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

    # Prepare user data with hashed password
    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["hashed_password"] = hash_password(user_data.password)

    user = await create_user(session, user_dict)

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
        dedent(f"""
            GET /users/ - Listing users
            - skip: {skip}
            - limit: {limit}
            - active_only: {active_only}
        """).strip()
    )
    filters = UserListFilter(skip=skip, limit=limit, active_only=active_only)
    users = await list_users(session, filters)
    logger.info(
        dedent(f"""
            Listed {len(users)} users
            - skip: {skip}
            - limit: {limit}
            - active_only: {active_only}
        """).strip()
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

    # Get only fields that were actually set
    update_dict = user_data.model_dump(exclude_unset=True)

    # Hash password if provided
    if "password" in update_dict:
        logger.debug(f"Hashing new password for user: {user_id}")
        update_dict["hashed_password"] = hash_password(update_dict["password"])
        del update_dict["password"]

    updated_user = await update_user(session, user, update_dict)

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
