"""Tests for YouTube downloader with mocked yt-dlp."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
import yt_dlp  # type: ignore[import-untyped]

from python.yt import (
    InvalidURLError,
    TranscriptionError,
    UnavailableVideoError,
    download_audio,
    download_video,
    get_transcriptions,
    get_video_info,
)
from python.yt.models import VideoInfo


def test_get_video_info_success(mock_video_info: dict[str, Any]) -> None:
    """Test successful video info extraction."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        info = get_video_info(url)

        assert isinstance(info, VideoInfo)
        assert info.video_id == "dQw4w9WgXcQ"
        assert "Rick Astley" in info.title
        assert "Never Gonna Give You Up" in info.title
        assert info.uploader == "Rick Astley"
        assert info.duration is not None
        assert 200 < info.duration < 220  # ~3.5 minutes
        assert info.view_count is not None
        assert info.view_count > 0
        assert len(info.formats) > 0
        assert len(info.thumbnails) > 0
        assert "Music" in info.categories
        assert any("rick" in tag.lower() or "astley" in tag.lower() for tag in info.tags)


def test_get_video_info_invalid_url() -> None:
    """Test extraction with invalid URL."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(
            "ERROR: Invalid URL"
        )
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        with pytest.raises(InvalidURLError) as exc_info:
            get_video_info("https://invalid-url")

        assert "Invalid URL" in str(exc_info.value)


def test_get_video_info_unavailable() -> None:
    """Test extraction with unavailable video."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(
            "Video unavailable"
        )
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        with pytest.raises(UnavailableVideoError) as exc_info:
            get_video_info("https://www.youtube.com/watch?v=deleted_video")

        assert "unavailable" in str(exc_info.value).lower()


def test_download_video_success(mock_video_info: dict[str, Any], tmp_path: Path) -> None:
    """Test successful video download."""
    output_path = tmp_path / "downloads"
    downloaded_file = output_path / "Rick Astley - Never Gonna Give You Up.mp4"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info
        mock_ydl.prepare_filename.return_value = str(downloaded_file)
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        info = download_video(url, output_path)

        assert isinstance(info, VideoInfo)
        assert info.video_id == "dQw4w9WgXcQ"
        assert info.downloaded_file == downloaded_file
        assert info.download_timestamp is not None
        mock_ydl.extract_info.assert_called_once_with(url, download=True)


def test_download_video_with_format(mock_video_info: dict[str, Any], tmp_path: Path) -> None:
    """Test video download with custom format."""
    output_path = tmp_path / "downloads"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info
        mock_ydl.prepare_filename.return_value = str(
            output_path / "video.mp4"
        )
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        format_selector = "bestvideo[height<=720]+bestaudio/best[height<=720]"
        info = download_video(url, output_path, format=format_selector)

        assert isinstance(info, VideoInfo)
        # Verify format was passed to YoutubeDL
        call_kwargs = mock_ydl_class.call_args[0][0]
        assert call_kwargs["format"] == format_selector


def test_download_audio_success(mock_video_info: dict[str, Any], tmp_path: Path) -> None:
    """Test successful audio download."""
    output_path = tmp_path / "music"
    downloaded_file = output_path / "Rick Astley - Never Gonna Give You Up.mp3"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info
        mock_ydl.prepare_filename.return_value = str(
            output_path / "Rick Astley - Never Gonna Give You Up.webm"
        )
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        info = download_audio(
            url, output_path, audio_format="mp3", audio_quality="320K"
        )

        assert isinstance(info, VideoInfo)
        assert info.video_id == "dQw4w9WgXcQ"
        assert info.downloaded_file == downloaded_file
        assert info.download_timestamp is not None

        # Verify postprocessor was configured
        call_kwargs = mock_ydl_class.call_args[0][0]
        assert "postprocessors" in call_kwargs
        postprocessor = call_kwargs["postprocessors"][0]
        assert postprocessor["key"] == "FFmpegExtractAudio"
        assert postprocessor["preferredcodec"] == "mp3"
        assert postprocessor["preferredquality"] == "320K"


def test_download_audio_with_m4a(mock_video_info: dict[str, Any], tmp_path: Path) -> None:
    """Test audio download with m4a format."""
    output_path = tmp_path / "music"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info
        mock_ydl.prepare_filename.return_value = str(output_path / "audio.webm")
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        info = download_audio(url, output_path, audio_format="m4a")

        assert info.downloaded_file is not None
        assert info.downloaded_file.suffix == ".m4a"

        # Verify format
        call_kwargs = mock_ydl_class.call_args[0][0]
        postprocessor = call_kwargs["postprocessors"][0]
        assert postprocessor["preferredcodec"] == "m4a"


def test_get_transcriptions_success(mock_video_info_with_subs: dict[str, Any]) -> None:
    """Test successful transcription extraction."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info_with_subs
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        transcriptions = get_transcriptions(url)

        # Should have transcriptions (real data has multiple formats per language)
        assert len(transcriptions) > 0

        # Check manual subtitles exist
        manual = [t for t in transcriptions if not t.auto_generated]
        assert len(manual) > 0

        # Get unique languages from manual subs
        manual_langs = {t.language for t in manual}
        assert "en" in manual_langs  # "Me at the zoo" has English subtitles


def test_get_transcriptions_with_language_filter(mock_video_info_with_subs: dict[str, Any]) -> None:
    """Test transcription extraction with language filter."""
    # Create custom mock with specific languages for filter testing
    mock_info_with_subs = {
        **mock_video_info_with_subs,
        "subtitles": {
            "en": [{"ext": "vtt", "url": "https://example.com/en.vtt"}],
            "es": [{"ext": "vtt", "url": "https://example.com/es.vtt"}],
            "fr": [{"ext": "vtt", "url": "https://example.com/fr.vtt"}],
        },
        "automatic_captions": {},
    }

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info_with_subs
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        transcriptions = get_transcriptions(url, languages=["en", "fr"])

        # Should only get en and fr
        assert len(transcriptions) == 2
        assert {t.language for t in transcriptions} == {"en", "fr"}


def test_get_transcriptions_error() -> None:
    """Test transcription extraction error handling."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = Exception("Unexpected error")
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        with pytest.raises(TranscriptionError) as exc_info:
            get_transcriptions("https://www.youtube.com/watch?v=test")

        assert "Unexpected error" in str(exc_info.value)


def test_download_video_creates_directory(mock_video_info: dict[str, Any], tmp_path: Path) -> None:
    """Test that download_video creates output directory if it doesn't exist."""
    output_path = tmp_path / "nonexistent" / "downloads"
    assert not output_path.exists()

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info
        mock_ydl.prepare_filename.return_value = str(output_path / "video.mp4")
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        download_video("https://www.youtube.com/watch?v=test", output_path)

        assert output_path.exists()
        assert output_path.is_dir()


def test_download_audio_creates_directory(mock_video_info: dict[str, Any], tmp_path: Path) -> None:
    """Test that download_audio creates output directory if it doesn't exist."""
    output_path = tmp_path / "nonexistent" / "music"
    assert not output_path.exists()

    with patch("yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_video_info
        mock_ydl.prepare_filename.return_value = str(output_path / "audio.webm")
        mock_ydl.__enter__ = Mock(return_value=mock_ydl)
        mock_ydl.__exit__ = Mock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        download_audio("https://www.youtube.com/watch?v=test", output_path)

        assert output_path.exists()
        assert output_path.is_dir()
