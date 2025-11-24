"""Tests for YouTube video information extraction.

This module tests the get_video_info function and related functionality.
"""


import pytest
import yt_dlp  # type: ignore[import-untyped]

from python.infra.youtube.client import get_video_info
from python.infra.youtube.exceptions import InvalidURLError, UnavailableVideoError
from python.infra.youtube.tests.helpers import (
    MockYoutubeDL,
    VideoInfoExpect,
    assert_video_info,
    generate_test_urls,
    make_mock_video_info_dict,
)


class TestGetVideoInfo:
    """Tests for get_video_info function."""

    @pytest.mark.asyncio
    async def test_get_video_info_success(self) -> None:
        """Test successful video info extraction."""
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(extract_info_return=mock_data) as mock_ydl:
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            info = await get_video_info(url)

            # Assert using helper
            expected = VideoInfoExpect(
                video_id="dQw4w9WgXcQ",
                title="Rick Astley - Never Gonna Give You Up",
                duration=212,
                view_count=1_000_000_000,
                uploader="Rick Astley",
                formats_count=3,
                thumbnails_count=2,
            )
            assert_video_info(info, expected)

            # Verify API was called correctly
            mock_ydl.extract_info.assert_called_once_with(url, download=False)

    @pytest.mark.asyncio
    async def test_get_video_info_minimal(self) -> None:
        """Test extraction with minimal video data."""
        mock_data = {
            "id": "minimal123",
            "title": "Minimal Video",
            "url": "https://www.youtube.com/watch?v=minimal123",
        }

        with MockYoutubeDL(extract_info_return=mock_data):
            info = await get_video_info("https://www.youtube.com/watch?v=minimal123")

            assert info.video_id == "minimal123"
            assert info.title == "Minimal Video"
            # Optional fields should be None or empty
            assert info.description is None
            assert info.duration is None
            assert info.formats == []

    @pytest.mark.asyncio
    async def test_get_video_info_with_rich_metadata(self) -> None:
        """Test extraction with comprehensive metadata."""
        mock_data = make_mock_video_info_dict(
            video_id="rich123",
            title="Rich Metadata Video",
            include_subtitles=True,
            include_auto_captions=True,
        )
        # Add extra metadata
        mock_data.update({
            "like_count": 50_000,
            "comment_count": 1_500,
            "is_live": False,
            "was_live": True,
            "age_limit": 18,
        })

        with MockYoutubeDL(extract_info_return=mock_data):
            info = await get_video_info("https://www.youtube.com/watch?v=rich123")

            assert info.video_id == "rich123"
            assert info.like_count == 50_000
            assert info.comment_count == 1_500
            assert info.was_live is True
            assert info.is_live is False
            assert info.age_limit == 18

    @pytest.mark.asyncio
    @pytest.mark.parametrize("url,description", generate_test_urls())
    async def test_get_video_info_various_urls(self, url: str, description: str) -> None:
        """Test video info extraction with various URL formats."""
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(extract_info_return=mock_data):
            info = await get_video_info(url)
            assert info.video_id == "dQw4w9WgXcQ", f"Failed for {description}"


class TestGetVideoInfoErrors:
    """Tests for error handling in get_video_info."""

    @pytest.mark.asyncio
    async def test_invalid_url_error(self) -> None:
        """Test extraction with invalid URL."""
        from unittest.mock import MagicMock, Mock, patch
        error = yt_dlp.utils.DownloadError("ERROR: Invalid URL")

        with patch("python.infra.youtube.client.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = error
            mock_ydl.__enter__ = Mock(return_value=mock_ydl)
            mock_ydl.__exit__ = Mock(return_value=False)
            mock_ydl_class.return_value = mock_ydl

            with pytest.raises(InvalidURLError):
                await get_video_info("https://invalid-url")

    @pytest.mark.asyncio
    async def test_unavailable_video_error(self) -> None:
        """Test extraction with unavailable video."""
        error = yt_dlp.utils.DownloadError("Video unavailable")

        with MockYoutubeDL(extract_info_side_effect=error), pytest.raises(
            UnavailableVideoError, match=r"(?i)unavailable"
        ):
            await get_video_info("https://www.youtube.com/watch?v=deleted_video")


    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self) -> None:
        """Test handling of unexpected errors."""
        error = Exception("Unexpected error occurred")

        with MockYoutubeDL(extract_info_side_effect=error):
            # Should propagate unexpected errors
            with pytest.raises(Exception) as exc_info:
                await get_video_info("https://www.youtube.com/watch?v=test")

            assert "Unexpected error occurred" in str(exc_info.value)
