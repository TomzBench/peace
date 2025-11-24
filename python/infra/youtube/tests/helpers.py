"""Test helpers and factory functions for YouTube tests.

This module provides reusable test utilities following the patterns from Whisper tests:
- Factory functions for creating mock data
- Assertion helpers for validating results
- Mock setup utilities to reduce duplication
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import yt_dlp  # type: ignore[import-untyped]
from pydantic import HttpUrl

from ..models import (
    Format,
    Thumbnail,
    Transcription,
    VideoInfo,
)


# Factory Functions for Mock Data
def make_mock_thumbnail(
    width: int = 1920,
    height: int = 1080,
    url: str = "https://i.ytimg.com/vi/test/maxresdefault.jpg",
) -> Thumbnail:
    """Create a mock Thumbnail object for testing.
    """
    return Thumbnail(url=HttpUrl(url), width=width, height=height)


def make_mock_format(
    format_id: str = "22",
    ext: str = "mp4",
    resolution: str = "1280x720",
    filesize: int | None = 10_000_000,
) -> Format:
    """Create a mock Format object for testing.
    """
    width, height = resolution.split("x") if "x" in resolution else (None, None)
    return Format(
        format_id=format_id,
        ext=ext,
        resolution=resolution,
        filesize=filesize,
        width=int(width) if width else None,
        height=int(height) if height else None,
        vcodec="avc1.42001E" if ext in ["mp4", "webm"] else None,
        acodec="mp4a.40.2" if ext in ["mp4", "m4a", "webm"] else None,
    )


def make_mock_transcription(
    language: str = "en",
    text: str | None = None,
    auto_generated: bool = False,
    ext: str = "vtt",
) -> Transcription:
    """Create a mock Transcription object for testing.
    """
    if text is None:
        gen_type = "auto-generated" if auto_generated else "manual"
        text = f"This is a {gen_type} transcription in {language}"
    return Transcription(
        language=language,
        text=text,
        auto_generated=auto_generated,
        ext=ext,
    )


def make_mock_video_info(
    video_id: str = "dQw4w9WgXcQ",
    title: str = "Rick Astley - Never Gonna Give You Up",
    duration: int = 212,
    view_count: int = 1_000_000,
    include_formats: bool = True,
    include_thumbnails: bool = True,
) -> VideoInfo:
    """Create a mock VideoInfo object for testing.
    """
    info = VideoInfo(
        url=HttpUrl(f"https://www.youtube.com/watch?v={video_id}"),
        id=video_id,  # Use alias 'id' instead of 'video_id'
        title=title,
        description="Test video description",
        uploader="Rick Astley",
        uploader_id="@RickAstleyYT",
        channel="Rick Astley",
        channel_id="UCuAXFkgsw1L7xaCfnd5JJOw",
        upload_date="20091024",
        timestamp=1256392800,
        duration=duration,
        view_count=view_count,
        like_count=10_000,
        comment_count=500,
        age_limit=0,
        is_live=False,
        was_live=False,
        categories=["Music"],
        tags=["rick", "astley", "never", "gonna", "give", "you", "up"],
    )

    if include_formats:
        info.formats = [
            make_mock_format("22", "mp4", "1280x720", 50_000_000),
            make_mock_format("18", "mp4", "640x360", 20_000_000),
            make_mock_format("140", "m4a", "", 5_000_000),
        ]

    if include_thumbnails:
        info.thumbnails = [
            make_mock_thumbnail(1920, 1080),
            make_mock_thumbnail(640, 480, "https://i.ytimg.com/vi/test/hqdefault.jpg"),
        ]

    return info


def make_mock_video_info_dict(
    video_id: str = "dQw4w9WgXcQ",
    title: str = "Rick Astley - Never Gonna Give You Up",
    include_subtitles: bool = False,
    include_auto_captions: bool = False,
) -> dict[str, Any]:
    """Create a mock video info dictionary as returned by yt-dlp.
    """
    info: dict[str, Any] = {
        "id": video_id,
        "title": title,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "description": "Test video description",
        "uploader": "Rick Astley",
        "uploader_id": "@RickAstleyYT",
        "channel": "Rick Astley",
        "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
        "upload_date": "20091024",
        "timestamp": 1256392800,
        "duration": 212,
        "view_count": 1_000_000_000,
        "like_count": 10_000_000,
        "comment_count": 500_000,
        "age_limit": 0,
        "is_live": False,
        "was_live": False,
        "categories": ["Music"],
        "tags": ["rick", "astley", "never", "gonna", "give", "you", "up"],
        "formats": [
            {
                "format_id": "22",
                "ext": "mp4",
                "resolution": "1280x720",
                "filesize": 50_000_000,
                "width": 1280,
                "height": 720,
                "vcodec": "avc1.42001E",
                "acodec": "mp4a.40.2",
                "tbr": 1500,
                "fps": 30,
            },
            {
                "format_id": "18",
                "ext": "mp4",
                "resolution": "640x360",
                "filesize": 20_000_000,
                "width": 640,
                "height": 360,
                "vcodec": "avc1.42001E",
                "acodec": "mp4a.40.2",
                "tbr": 500,
                "fps": 30,
            },
            {
                "format_id": "140",
                "ext": "m4a",
                "filesize": 5_000_000,
                "acodec": "mp4a.40.2",
                "tbr": 128,
            },
        ],
        "thumbnails": [
            {
                "url": "https://i.ytimg.com/vi/test/maxresdefault.jpg",
                "width": 1920,
                "height": 1080,
            },
            {
                "url": "https://i.ytimg.com/vi/test/hqdefault.jpg",
                "width": 640,
                "height": 480,
            },
        ],
    }

    if include_subtitles:
        info["subtitles"] = {
            "en": [
                {
                    "ext": "vtt",
                    "url": "https://example.com/en.vtt",
                    "content": "English subtitle text with elephants and trunks",
                }
            ],
            "es": [
                {
                    "ext": "vtt",
                    "url": "https://example.com/es.vtt",
                    "content": "Spanish subtitle text",
                }
            ],
        }

    if include_auto_captions:
        info["automatic_captions"] = {
            "en": [
                {
                    "ext": "vtt",
                    "url": "https://example.com/auto_en.vtt",
                    "content": "[Auto-generated] English captions",
                }
            ],
        }

    return info


# Mock Setup Utilities
class MockYoutubeDL:
    """Context manager for mocking YoutubeDL with common setup."""

    def __init__(
        self,
        extract_info_return: dict[str, Any] | None = None,
        extract_info_side_effect: Exception | None = None,
        prepare_filename_return: str | None = None,
    ) -> None:
        """Initialize mock YoutubeDL context manager.

        Args:
            extract_info_return: Value to return from extract_info
            extract_info_side_effect: Exception to raise from extract_info
            prepare_filename_return: Value to return from prepare_filename
        """
        self.extract_info_return = extract_info_return or make_mock_video_info_dict()
        self.extract_info_side_effect = extract_info_side_effect
        self.prepare_filename_return = prepare_filename_return
        self.mock_ydl: MagicMock | None = None
        self.patcher = None

    def __enter__(self) -> MagicMock:
        """Enter context manager and return configured mock."""
        from unittest.mock import patch

        # Patch where it's used, not where it's defined
        self.patcher = patch("python.infra.youtube.client.yt_dlp.YoutubeDL")  # type: ignore[assignment]
        mock_ydl_class = self.patcher.__enter__()  # type: ignore[attr-defined]

        self.mock_ydl = MagicMock()

        # Configure extract_info
        if self.extract_info_side_effect:
            self.mock_ydl.extract_info.side_effect = self.extract_info_side_effect
        else:
            self.mock_ydl.extract_info.return_value = self.extract_info_return

        # Configure prepare_filename
        if self.prepare_filename_return:
            self.mock_ydl.prepare_filename.return_value = self.prepare_filename_return

        # Configure context manager behavior
        self.mock_ydl.__enter__ = Mock(return_value=self.mock_ydl)
        self.mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = self.mock_ydl

        return self.mock_ydl

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and clean up patch."""
        if self.patcher:
            self.patcher.__exit__(*args)


# Assertion Helpers
@dataclass
class VideoInfoExpect:
    """Expected VideoInfo values for assertions."""

    video_id: str
    title: str
    duration: int | None = None
    view_count: int | None = None
    uploader: str | None = None
    downloaded_file: Path | None = None
    formats_count: int | None = None
    thumbnails_count: int | None = None


def assert_video_info(actual: VideoInfo, expected: VideoInfoExpect) -> None:
    """Assert VideoInfo matches expected values.

    Raises AssertionError.

    """
    assert actual.video_id == expected.video_id, (
        f"video_id mismatch: {actual.video_id} != {expected.video_id}"
    )
    assert actual.title == expected.title, f"title mismatch: {actual.title} != {expected.title}"

    if expected.duration is not None:
        assert actual.duration == expected.duration, (
            f"duration mismatch: {actual.duration} != {expected.duration}"
        )

    if expected.view_count is not None:
        assert actual.view_count == expected.view_count, (
            f"view_count mismatch: {actual.view_count} != {expected.view_count}"
        )

    if expected.uploader is not None:
        assert actual.uploader == expected.uploader, (
            f"uploader mismatch: {actual.uploader} != {expected.uploader}"
        )

    if expected.downloaded_file is not None:
        assert actual.downloaded_file == expected.downloaded_file, (
            f"downloaded_file mismatch: {actual.downloaded_file} != {expected.downloaded_file}"
        )

    if expected.formats_count is not None:
        assert len(actual.formats) == expected.formats_count, (
            f"formats count mismatch: {len(actual.formats)} != {expected.formats_count}"
        )

    if expected.thumbnails_count is not None:
        assert len(actual.thumbnails) == expected.thumbnails_count, (
            f"thumbnails count mismatch: {len(actual.thumbnails)} != {expected.thumbnails_count}"
        )


def assert_transcriptions(
    transcriptions: list[Transcription],
    expected_languages: list[str] | None = None,
    expected_count: int | None = None,
    has_manual: bool | None = None,
    has_auto: bool | None = None,
) -> None:
    """Assert transcriptions match expected criteria.

    Raises AssertionError.

    """
    if expected_count is not None:
        assert len(transcriptions) == expected_count, (
            f"Count mismatch: {len(transcriptions)} != {expected_count}"
        )

    if expected_languages is not None:
        actual_languages = {t.language for t in transcriptions}
        expected_set = set(expected_languages)
        assert actual_languages == expected_set, (
            f"Languages mismatch: {actual_languages} != {expected_set}"
        )

    if has_manual is not None:
        manual_exists = any(not t.auto_generated for t in transcriptions)
        assert manual_exists == has_manual, (
            f"Manual subtitles: expected {has_manual}, got {manual_exists}"
        )

    if has_auto is not None:
        auto_exists = any(t.auto_generated for t in transcriptions)
        assert auto_exists == has_auto, f"Auto captions: expected {has_auto}, got {auto_exists}"


def assert_download_options(
    ydl_opts: dict[str, Any],
    expected_format: str | None = None,
    has_postprocessor: bool | None = None,
    audio_codec: str | None = None,
    audio_quality: str | None = None,
) -> None:
    """Assert YoutubeDL options match expected configuration.

    Raises AssertionError.

    """
    if expected_format is not None:
        assert "format" in ydl_opts, "Format not in options"
        assert ydl_opts["format"] == expected_format, (
            f"Format mismatch: {ydl_opts['format']} != {expected_format}"
        )

    if has_postprocessor is not None:
        has_pp = "postprocessors" in ydl_opts and len(ydl_opts["postprocessors"]) > 0
        assert has_pp == has_postprocessor, (
            f"Postprocessor presence: expected {has_postprocessor}, got {has_pp}"
        )

    if audio_codec is not None or audio_quality is not None:
        assert "postprocessors" in ydl_opts, "No postprocessors found"
        pp = ydl_opts["postprocessors"][0]

        if audio_codec is not None:
            assert pp.get("preferredcodec") == audio_codec, (
                f"Codec mismatch: {pp.get('preferredcodec')} != {audio_codec}"
            )

        if audio_quality is not None:
            assert pp.get("preferredquality") == audio_quality, (
                f"Quality mismatch: {pp.get('preferredquality')} != {audio_quality}"
            )


# Test Data Generators
def generate_test_urls() -> list[tuple[str, str]]:
    """Generate various YouTube URLs for testing.

    Returns:
        List of (url, description) tuples
    """
    return [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "Standard watch URL"),
        ("https://youtu.be/dQw4w9WgXcQ", "Short URL"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s", "URL with timestamp"),
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
            "URL with playlist",
        ),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "Mobile URL"),
    ]


def generate_error_scenarios() -> list[tuple[str, type[Exception], str]]:
    """Generate error scenarios for testing.

    Returns:
        List of (error_message, exception_type, description) tuples
    """
    return [
        ("ERROR: Invalid URL", yt_dlp.utils.DownloadError, "Invalid URL format"),
        ("Video unavailable", yt_dlp.utils.DownloadError, "Video is unavailable"),
        ("Private video", yt_dlp.utils.DownloadError, "Video is private"),
        (
            "This video is not available in your country",
            yt_dlp.utils.DownloadError,
            "Geo-blocked video",
        ),
        ("ERROR: Unable to extract video data", yt_dlp.utils.DownloadError, "Extraction failure"),
    ]
