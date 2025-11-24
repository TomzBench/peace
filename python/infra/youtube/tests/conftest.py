"""Pytest configuration and shared fixtures for YouTube tests.

This module provides comprehensive test fixtures following patterns from Whisper tests:
- Factory-based fixtures for creating mock data
- Cached fixture loading for performance
- Parametrized fixtures for various test scenarios
"""

import json
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
import pytest_asyncio
import yt_dlp  # type: ignore[import-untyped]

from ..models import VideoInfo
from .helpers import (
    make_mock_format,
    make_mock_thumbnail,
    make_mock_transcription,
    make_mock_video_info,
    make_mock_video_info_dict,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Cache loaded fixtures to avoid repeated file I/O
_fixture_cache: dict[str, dict[str, Any]] = {}


def load_fixture(filename: str) -> dict[str, Any]:
    """Load a JSON fixture file from the fixtures directory.

    Raises FileNotFoundError.

    """
    if filename in _fixture_cache:
        return _fixture_cache[filename]

    filepath = FIXTURES_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Fixture not found: {filepath}\n"
            f"Run 'python -m python.infra.youtube.tests.update_fixtures' to generate fixtures."
        )

    with open(filepath) as f:
        data: dict[str, Any] = json.load(f)

    _fixture_cache[filename] = data
    return data


# Basic Fixtures
@pytest.fixture
def mock_video_info() -> dict[str, Any]:
    """Fixture providing basic video info from filesystem.

    Returns:
        Video info dict loaded from video_basic.json
    """
    return load_fixture("video_basic.json")


@pytest.fixture
def mock_video_info_with_subs() -> dict[str, Any]:
    """Fixture providing video info with subtitles from filesystem.

    Returns:
        Video info dict loaded from video_with_subs.json
    """
    return load_fixture("video_with_subs.json")


# Factory-based Fixtures
@pytest.fixture
def video_info_factory() -> Callable[..., VideoInfo]:
    """Fixture providing factory function for VideoInfo objects.

    Returns:
        Factory function for creating mock VideoInfo
    """
    return make_mock_video_info


@pytest.fixture
def video_dict_factory() -> Callable[..., dict[str, Any]]:
    """Fixture providing factory function for video info dicts.

    Returns:
        Factory function for creating mock video info dicts
    """
    return make_mock_video_info_dict


@pytest.fixture
def format_factory() -> Callable[..., Any]:
    """Fixture providing factory function for Format objects.

    Returns:
        Factory function for creating mock Format objects
    """
    return make_mock_format


@pytest.fixture
def thumbnail_factory() -> Callable[..., Any]:
    """Fixture providing factory function for Thumbnail objects.

    Returns:
        Factory function for creating mock Thumbnail objects
    """
    return make_mock_thumbnail


@pytest.fixture
def transcription_factory() -> Callable[..., Any]:
    """Fixture providing factory function for Transcription objects.

    Returns:
        Factory function for creating mock Transcription objects
    """
    return make_mock_transcription


# Mock YoutubeDL Fixtures
@pytest.fixture
def mock_ydl_success() -> MagicMock:
    """Fixture providing a successful YoutubeDL mock.

    Returns:
        Configured mock YoutubeDL instance
    """
    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = make_mock_video_info_dict()
    mock_ydl.prepare_filename.return_value = "/tmp/video.mp4"
    mock_ydl.__enter__ = Mock(return_value=mock_ydl)
    mock_ydl.__exit__ = Mock(return_value=False)
    return mock_ydl


@pytest.fixture
def mock_ydl_error() -> MagicMock:
    """Fixture providing a YoutubeDL mock that raises errors.

    Returns:
        Mock YoutubeDL that raises DownloadError
    """
    mock_ydl = MagicMock()
    mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("Test error")
    mock_ydl.__enter__ = Mock(return_value=mock_ydl)
    mock_ydl.__exit__ = Mock(return_value=False)
    return mock_ydl


# Test Data Fixtures
@pytest.fixture
def sample_video_url() -> str:
    """Fixture providing a sample YouTube URL.

    Returns:
        Standard YouTube watch URL
    """
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def sample_video_urls() -> list[str]:
    """Fixture providing various YouTube URL formats.

    Returns:
        List of different YouTube URL formats
    """
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
    ]


@pytest.fixture
def sample_languages() -> list[str]:
    """Fixture providing common language codes.

    Returns:
        List of ISO language codes
    """
    return ["en", "es", "fr", "de", "ja", "ko", "zh"]


@pytest.fixture
def sample_video_info() -> VideoInfo:
    """Fixture providing a sample VideoInfo object.

    Returns:
        Mock VideoInfo instance with typical data
    """
    return make_mock_video_info(
        video_id="sample123",
        title="Sample Video",
        duration=300,
        view_count=100_000,
    )


@pytest.fixture
def download_timestamp() -> datetime:
    """Fixture providing a consistent timestamp for downloads.

    Returns:
        Fixed datetime for testing
    """
    return datetime(2024, 1, 1, 12, 0, 0)


# Path Fixtures
@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary output directory.
    """
    output = tmp_path / "output"
    output.mkdir(exist_ok=True)
    return output


@pytest.fixture
def video_output_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary video output directory.
    """
    output = tmp_path / "videos"
    output.mkdir(exist_ok=True)
    return output


@pytest.fixture
def audio_output_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary audio output directory.
    """
    output = tmp_path / "audio"
    output.mkdir(exist_ok=True)
    return output


# Async Fixtures for executor management
@pytest_asyncio.fixture
async def mock_executor() -> AsyncIterator[ThreadPoolExecutor]:
    """Provide a test executor with limited workers."""
    executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="test_youtube_")
    yield executor
    executor.shutdown(wait=True)
