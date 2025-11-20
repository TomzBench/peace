"""User domain models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from python.domain.video.models import Video


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

    # Relationship to videos through junction table
    user_videos: list["UserVideo"] = Relationship(back_populates="user")


class UserVideo(SQLModel, table=True):
    """Junction table linking users to their downloaded videos.

    Enables many-to-many: one user can have many videos,
    one video can belong to many users.
    """

    __tablename__ = "user_videos"

    # Composite primary key
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    video_id: int = Field(foreign_key="videos.id", primary_key=True)

    # When user added this video to their collection
    added_at: datetime = Field(default_factory=datetime.utcnow)

    # Optional: user's personal notes about this video
    notes: str | None = Field(default=None, max_length=1000)

    # Relationships
    user: User = Relationship(back_populates="user_videos")
    video: "Video" = Relationship(back_populates="user_videos")


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
