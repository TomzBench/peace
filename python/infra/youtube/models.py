"""Pydantic models for YouTube data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Thumbnail(BaseModel):
    """YouTube video thumbnail."""

    url: HttpUrl
    width: int | None = None
    height: int | None = None


class Format(BaseModel):
    """Video or audio format information."""

    format_id: str
    ext: str
    format_note: str | None = None
    filesize: int | None = None
    filesize_approx: int | None = None
    tbr: float | None = None  # Total bitrate
    vcodec: str | None = None  # Video codec
    acodec: str | None = None  # Audio codec
    fps: float | None = None
    width: int | None = None
    height: int | None = None
    resolution: str | None = None


class Transcription(BaseModel):
    """Video transcription/subtitle."""

    language: str
    text: str
    auto_generated: bool = False
    ext: str = "vtt"


class VideoInfo(BaseModel):
    """Complete video metadata and download information."""

    # Basic info
    url: HttpUrl
    video_id: str
    title: str
    description: str | None = None
    uploader: str | None = None
    uploader_id: str | None = None
    channel: str | None = None
    channel_id: str | None = None

    # Timestamps
    upload_date: str | None = None  # YYYYMMDD format from yt-dlp
    timestamp: int | None = None  # Unix timestamp
    duration: int | None = None  # Duration in seconds

    # Media info
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    age_limit: int = 0
    is_live: bool = False
    was_live: bool = False

    # Available formats
    formats: list[Format] = Field(default_factory=list)
    thumbnails: list[Thumbnail] = Field(default_factory=list)

    # Categories/tags
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Download info (populated after download)
    downloaded_file: Path | None = None
    download_timestamp: datetime | None = None


class DownloadOptions(BaseModel):
    """Options for downloading videos/audio."""

    format: str = "best"  # yt-dlp format selector
    extract_audio: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192K"
    output_template: str = "%(title)s.%(ext)s"
    write_subtitles: bool = False
    write_auto_subtitles: bool = False
    subtitle_langs: list[str] = Field(default_factory=lambda: ["en"])
    quiet: bool = True
    no_warnings: bool = False
    progress_hooks: list = Field(default_factory=list)


@dataclass
class VideoDownloadOptions:
    """Options for downloading videos."""

    format: str = "best"
    ydl_opts: dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioDownloadOptions:
    """Options for downloading audio."""

    format: str = "mp3"
    quality: str = "192K"
    ydl_opts: dict[str, Any] = field(default_factory=dict)
