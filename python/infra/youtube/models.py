"""Pydantic models for YouTube data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Thumbnail(BaseModel):
    """YouTube video thumbnail."""

    model_config = ConfigDict(extra="ignore")

    url: HttpUrl
    width: int | None = None
    height: int | None = None

    def __repr__(self) -> str:
        dims = f"{self.width}x{self.height}" if self.width and self.height else "unknown"
        return f"Thumbnail(url={str(self.url)!r}, dimensions={dims})"


class Format(BaseModel):
    """Video or audio format information."""

    model_config = ConfigDict(extra="ignore")

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

    def __repr__(self) -> str:
        parts = [f"id={self.format_id}", f"ext={self.ext}"]
        if self.resolution:
            parts.append(f"res={self.resolution}")
        elif self.width and self.height:
            parts.append(f"res={self.width}x{self.height}")
        if self.format_note:
            parts.append(f"note={self.format_note!r}")
        if self.filesize:
            mb = self.filesize / (1024 * 1024)
            parts.append(f"size={mb:.1f}MB")
        return f"Format({', '.join(parts)})"


class Transcription(BaseModel):
    """Video transcription/subtitle."""

    language: str
    text: str
    auto_generated: bool = False
    ext: str = "vtt"

    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        auto = "auto" if self.auto_generated else "manual"
        return (
            f"Transcription(lang={self.language!r}, {auto}, "
            f"ext={self.ext!r}, text={text_preview!r})"
        )


class VideoInfo(BaseModel):
    """Complete video metadata and download information."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # Basic info
    url: HttpUrl
    video_id: str = Field(alias="id")
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

    def __repr__(self) -> str:
        parts = [
            f"id={self.video_id!r}",
            f"title={self.title[:30]!r}..." if len(self.title) > 30 else f"title={self.title!r}",
        ]
        if self.duration:
            mins = self.duration // 60
            secs = self.duration % 60
            parts.append(f"duration={mins}:{secs:02d}")
        if self.view_count:
            if self.view_count >= 1_000_000:
                parts.append(f"views={self.view_count/1_000_000:.1f}M")
            elif self.view_count >= 1_000:
                parts.append(f"views={self.view_count/1_000:.1f}K")
            else:
                parts.append(f"views={self.view_count}")
        if self.downloaded_file:
            parts.append(f"downloaded={self.downloaded_file.name}")
        return f"VideoInfo({', '.join(parts)})"


@dataclass
class VideoDownloadOptions:
    """Options for downloading videos."""

    format: str = "best"
    ydl_opts: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        opts_count = len(self.ydl_opts)
        return f"VideoDownloadOptions(format={self.format!r}, ydl_opts={{{opts_count} items}})"


@dataclass
class AudioDownloadOptions:
    """Options for downloading audio."""

    format: str = "mp3"
    quality: str = "192K"
    ydl_opts: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        opts_count = len(self.ydl_opts)
        return (
            f"AudioDownloadOptions(format={self.format!r}, "
            f"quality={self.quality!r}, ydl_opts={{{opts_count} items}})"
        )
