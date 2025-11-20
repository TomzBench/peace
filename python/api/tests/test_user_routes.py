"""Tests for User API routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient) -> None:
    """Test creating a user via API."""
    response = await client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert "id" in data
    # Password should not be in response
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient) -> None:
    """Test creating a user with duplicate email fails."""
    # Create first user
    await client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser1",
            "password": "password123",
        },
    )

    # Try to create second user with same email
    response = await client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser2",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient) -> None:
    """Test getting a user by ID."""
    # Create a user
    create_response = await client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    # Get the user
    response = await client.get(f"/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent user."""
    response = await client.get("/users/99999")

    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient) -> None:
    """Test listing users."""
    # Create multiple users
    for i in range(3):
        await client.post(
            "/users/",
            json={
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "password": "password123",
            },
        )

    # List users
    response = await client.get("/users/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("email" in user for user in data)


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient) -> None:
    """Test listing users with pagination."""
    # Create 5 users
    for i in range(5):
        await client.post(
            "/users/",
            json={
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "password": "password123",
            },
        )

    # Get first 2 users
    response = await client.get("/users/?skip=0&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Get next 2 users
    response = await client.get("/users/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient) -> None:
    """Test updating a user."""
    # Create a user
    create_response = await client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    # Update the user
    response = await client.patch(
        f"/users/{user_id}",
        json={"full_name": "Updated Name"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "test@example.com"  # Unchanged


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient) -> None:
    """Test updating a non-existent user."""
    response = await client.patch(
        "/users/99999",
        json={"full_name": "Updated Name"},
    )

    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient) -> None:
    """Test deleting a user."""
    # Create a user
    create_response = await client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    # Delete the user
    response = await client.delete(f"/users/{user_id}")

    assert response.status_code == 204

    # Verify user is deleted
    get_response = await client.get(f"/users/{user_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent user."""
    response = await client.delete("/users/99999")

    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
