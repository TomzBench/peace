"""User model for SQL database."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User database model."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    """Schema for creating a user."""

    email: str = Field(max_length=255)
    username: str = Field(max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8)


class UserUpdate(SQLModel):
    """Schema for updating a user."""

    email: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8)


class UserRead(SQLModel):
    """Schema for reading a user (public view)."""

    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    created_at: datetime
