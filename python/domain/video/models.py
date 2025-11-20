"""Video domain models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from python.domain.user.models import UserVideo


class Video(SQLModel, table=True):
    """Video database model.

    Stores metadata for downloaded YouTube videos.
    Videos are shared across users (deduplicated by video_id).
    """

    __tablename__ = "videos"

    id: int | None = Field(default=None, primary_key=True)

    # YouTube video ID (unique identifier)
    video_id: str = Field(unique=True, index=True, max_length=20)

    # Metadata
    title: str = Field(max_length=500)
    description: str | None = Field(default=None)
    url: str = Field(max_length=500)
    uploader: str | None = Field(default=None, max_length=255)
    channel: str | None = Field(default=None, max_length=255)

    # Video properties
    duration: int | None = Field(default=None)  # Duration in seconds
    view_count: int | None = Field(default=None)
    upload_date: str | None = Field(default=None, max_length=8)  # YYYYMMDD format

    # Download info
    downloaded_file: str | None = Field(default=None, max_length=1000)  # File path
    file_size: int | None = Field(default=None)  # Size in bytes

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user_videos: list["UserVideo"] = Relationship(back_populates="video")
    summaries: list["Summary"] = Relationship(back_populates="video")


class Summary(SQLModel, table=True):
    """AI-generated summary of video content.

    Summaries are cached to avoid regenerating on each request.
    """

    __tablename__ = "summaries"

    id: int | None = Field(default=None, primary_key=True)

    # Foreign key to video
    video_id: int = Field(foreign_key="videos.id", index=True)

    # Summary content
    summary_text: str = Field(max_length=5000)

    # Model that generated this summary
    model_name: str = Field(max_length=100)  # e.g., "gpt-4", "claude-3-opus"

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    video: Video = Relationship(back_populates="summaries")


class VideoCreate(SQLModel):
    """Schema for creating a video."""

    video_id: str = Field(max_length=20)
    title: str = Field(max_length=500)
    description: str | None = None
    url: str = Field(max_length=500)
    uploader: str | None = Field(default=None, max_length=255)
    channel: str | None = Field(default=None, max_length=255)
    duration: int | None = None
    view_count: int | None = None
    upload_date: str | None = Field(default=None, max_length=8)
    downloaded_file: str | None = Field(default=None, max_length=1000)
    file_size: int | None = None


class VideoRead(SQLModel):
    """Schema for reading a video."""

    id: int
    video_id: str
    title: str
    description: str | None
    url: str
    uploader: str | None
    channel: str | None
    duration: int | None
    view_count: int | None
    upload_date: str | None
    downloaded_file: str | None
    file_size: int | None
    created_at: datetime
    updated_at: datetime


class SummaryCreate(SQLModel):
    """Schema for creating a summary."""

    video_id: int
    summary_text: str = Field(max_length=5000)
    model_name: str = Field(max_length=100)


class SummaryRead(SQLModel):
    """Schema for reading a summary."""

    id: int
    video_id: int
    summary_text: str
    model_name: str
    created_at: datetime
