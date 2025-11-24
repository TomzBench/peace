"""Tests for YouTube video and audio download functionality.

This module tests download_video and download_audio functions.
"""

from pathlib import Path

import pytest

from python.infra.youtube.client import download_audio, download_video
from python.infra.youtube.models import AudioDownloadOptions, VideoDownloadOptions
from python.infra.youtube.tests.helpers import (
    MockYoutubeDL,
    VideoInfoExpect,
    assert_download_options,
    assert_video_info,
    make_mock_video_info_dict,
)


class TestDownloadVideo:
    """Tests for download_video function."""

    @pytest.mark.asyncio
    async def test_download_video_success(self, tmp_path: Path) -> None:
        """Test successful video download."""
        output_path = tmp_path / "downloads"
        downloaded_file = output_path / "Rick Astley - Never Gonna Give You Up.mp4"
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(downloaded_file),
        ) as mock_ydl:
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            info = await download_video(url, output_path)

            # Verify video info
            expected = VideoInfoExpect(
                video_id="dQw4w9WgXcQ",
                title="Rick Astley - Never Gonna Give You Up",
                downloaded_file=downloaded_file,
            )
            assert_video_info(info, expected)
            assert info.download_timestamp is not None

            # Verify YoutubeDL was called with download=True
            mock_ydl.extract_info.assert_called_once_with(url, download=True)

    @pytest.mark.asyncio
    async def test_download_video_with_format(self, tmp_path: Path) -> None:
        """Test video download with custom format."""
        output_path = tmp_path / "downloads"
        mock_data = make_mock_video_info_dict()
        format_selector = "bestvideo[height<=720]+bestaudio/best[height<=720]"

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "video.mp4"),
        ) as mock_ydl:
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            options = VideoDownloadOptions(format=format_selector)

            # Capture the YoutubeDL init args by patching the constructor
            from unittest.mock import patch
            with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
                # Return our mock object that works correctly
                mock_ydl_class.return_value = mock_ydl

                info = await download_video(url, output_path, options)

                # Verify the format was passed to YoutubeDL constructor
                assert mock_ydl_class.called
                call_kwargs = mock_ydl_class.call_args[0][0]
                assert_download_options(
                    call_kwargs,
                    expected_format=format_selector,
                )

            # Verify we got valid info back
            assert info.video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_download_video_custom_options(self, tmp_path: Path) -> None:
        """Test video download with custom ydl_opts."""
        output_path = tmp_path / "downloads"
        mock_data = make_mock_video_info_dict()

        custom_opts = {
            "quiet": True,
            "no_warnings": True,
            "writesubtitles": True,
        }
        options = VideoDownloadOptions(
            format="best[height<=1080]",
            ydl_opts=custom_opts,
        )

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "video.mp4"),
        ):
            info = await download_video(
                "https://www.youtube.com/watch?v=test",
                output_path,
                options,
            )

            assert info.video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_download_video_creates_directory(self, tmp_path: Path) -> None:
        """Test that download_video creates output directory if it doesn't exist."""
        output_path = tmp_path / "nonexistent" / "downloads"
        assert not output_path.exists()

        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "video.mp4"),
        ):
            await download_video("https://www.youtube.com/watch?v=test", output_path)

            assert output_path.exists()
            assert output_path.is_dir()


class TestDownloadAudio:
    """Tests for download_audio function."""

    @pytest.mark.asyncio
    async def test_download_audio_success(self, tmp_path: Path) -> None:
        """Test successful audio download."""
        output_path = tmp_path / "music"
        downloaded_file = output_path / "Rick Astley - Never Gonna Give You Up.mp3"
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(
                output_path / "Rick Astley - Never Gonna Give You Up.webm"
            ),
        ) as mock_ydl:
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            options = AudioDownloadOptions(format="mp3", quality="320K")
            info = await download_audio(url, output_path, options)

            # Verify result
            expected = VideoInfoExpect(
                video_id="dQw4w9WgXcQ",
                title="Rick Astley - Never Gonna Give You Up",
                downloaded_file=downloaded_file,
            )
            assert_video_info(info, expected)
            assert info.download_timestamp is not None

            # Verify postprocessor configuration
            from unittest.mock import patch

            with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
                mock_ydl_class.return_value = mock_ydl
                await download_audio(url, output_path, options)
                call_kwargs = mock_ydl_class.call_args[0][0]
                assert_download_options(
                    call_kwargs,
                    has_postprocessor=True,
                    audio_codec="mp3",
                    audio_quality="320K",
                )

    @pytest.mark.asyncio
    async def test_download_audio_with_m4a(self, tmp_path: Path) -> None:
        """Test audio download with m4a format."""
        output_path = tmp_path / "music"
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "audio.webm"),
        ):
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            options = AudioDownloadOptions(format="m4a")
            info = await download_audio(url, output_path, options)

            assert info.downloaded_file is not None
            assert info.downloaded_file.suffix == ".m4a"

    @pytest.mark.asyncio
    async def test_download_audio_quality_options(self, tmp_path: Path) -> None:
        """Test audio download with various quality settings."""
        output_path = tmp_path / "music"
        mock_data = make_mock_video_info_dict()

        qualities = ["128K", "192K", "256K", "320K"]
        for quality in qualities:
            with MockYoutubeDL(
                extract_info_return=mock_data,
                prepare_filename_return=str(output_path / f"audio_{quality}.webm"),
            ):
                options = AudioDownloadOptions(format="mp3", quality=quality)
                info = await download_audio(
                    "https://www.youtube.com/watch?v=test",
                    output_path,
                    options,
                )
                assert info.downloaded_file is not None

    @pytest.mark.asyncio
    async def test_download_audio_creates_directory(self, tmp_path: Path) -> None:
        """Test that download_audio creates output directory if it doesn't exist."""
        output_path = tmp_path / "nonexistent" / "music"
        assert not output_path.exists()

        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "audio.webm"),
        ):
            await download_audio("https://www.youtube.com/watch?v=test", output_path)

            assert output_path.exists()
            assert output_path.is_dir()

    @pytest.mark.asyncio
    async def test_download_audio_custom_ydl_opts(self, tmp_path: Path) -> None:
        """Test audio download with custom ydl_opts."""
        output_path = tmp_path / "music"
        mock_data = make_mock_video_info_dict()

        custom_opts = {
            "prefer_ffmpeg": True,
            "keepvideo": False,
            "writethumbnail": True,
        }
        options = AudioDownloadOptions(
            format="opus",
            quality="160K",
            ydl_opts=custom_opts,
        )

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "audio.webm"),
        ):
            info = await download_audio(
                "https://www.youtube.com/watch?v=test",
                output_path,
                options,
            )

            assert info.video_id == "dQw4w9WgXcQ"
            assert info.downloaded_file is not None
            assert info.downloaded_file.suffix == ".opus"


class TestDownloadEdgeCases:
    """Test edge cases and error conditions for downloads."""

    @pytest.mark.asyncio
    async def test_download_video_with_default_path(self) -> None:
        """Test download_video with default output path."""
        mock_data = make_mock_video_info_dict()
        default_path = Path.cwd()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(default_path / "video.mp4"),
        ):
            info = await download_video("https://www.youtube.com/watch?v=test", Path.cwd())
            assert info.video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_download_audio_without_options(self, tmp_path: Path) -> None:
        """Test download_audio with default options."""
        output_path = tmp_path / "music"
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "audio.webm"),
        ):
            # Should use default AudioDownloadOptions
            info = await download_audio(
                "https://www.youtube.com/watch?v=test",
                output_path,
            )

            assert info.downloaded_file is not None
            # Default format is mp3
            assert info.downloaded_file.suffix == ".mp3"
