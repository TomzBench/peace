"""Pytest configuration and shared fixtures for YouTube tests."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Cache loaded fixtures to avoid repeated file I/O
_fixture_cache: dict[str, dict[str, Any]] = {}


def load_fixture(filename: str) -> dict[str, Any]:
    """Load a JSON fixture file from the fixtures directory.

    Args:
        filename: Name of fixture file (e.g., "video_basic.json")

    Returns:
        Parsed JSON data as dict

    Raises:
        FileNotFoundError: If fixture file doesn't exist

    Examples:
        >>> data = load_fixture("video_basic.json")
        >>> print(data["title"])
    """
    if filename in _fixture_cache:
        return _fixture_cache[filename]

    filepath = FIXTURES_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Fixture not found: {filepath}\n"
            f"Run 'python -m python.yt.tests.update_fixtures' to generate fixtures."
        )

    with open(filepath) as f:
        data: dict[str, Any] = json.load(f)

    _fixture_cache[filename] = data
    return data


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
