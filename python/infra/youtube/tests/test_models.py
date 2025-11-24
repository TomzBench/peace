"""Tests for YouTube models.

This module tests all Pydantic models and dataclasses used in the YouTube module,
following patterns from the Whisper test suite.
"""

from dataclasses import fields
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import HttpUrl, ValidationError

from python.infra.youtube.models import (
    AudioDownloadOptions,
    Format,
    Thumbnail,
    Transcription,
    VideoDownloadOptions,
    VideoInfo,
)
from python.infra.youtube.tests.helpers import (
    make_mock_format,
    make_mock_thumbnail,
    make_mock_transcription,
    make_mock_video_info,
)


class TestThumbnail:
    """Tests for Thumbnail model."""

    def test_thumbnail_creation(self) -> None:
        """Test creating a basic Thumbnail model."""
        thumbnail = Thumbnail(
            url=HttpUrl("https://i.ytimg.com/vi/test/maxresdefault.jpg"),
            width=1920,
            height=1080,
        )

        assert str(thumbnail.url) == "https://i.ytimg.com/vi/test/maxresdefault.jpg"
        assert thumbnail.width == 1920
        assert thumbnail.height == 1080

    def test_thumbnail_optional_dimensions(self) -> None:
        """Test Thumbnail with optional width/height."""
        thumbnail = Thumbnail(
            url=HttpUrl("https://i.ytimg.com/vi/test/default.jpg")
        )

        assert thumbnail.width is None
        assert thumbnail.height is None


    def test_thumbnail_factory(self) -> None:
        """Test thumbnail factory function from helpers."""
        thumbnail = make_mock_thumbnail(width=1280, height=720)

        assert thumbnail.width == 1280
        assert thumbnail.height == 720
        assert "ytimg.com" in str(thumbnail.url)


class TestFormat:
    """Tests for Format model."""

    def test_format_creation_basic(self) -> None:
        """Test creating a basic Format model."""
        fmt = Format(
            format_id="22",
            ext="mp4",
            format_note="720p",
            filesize=50_000_000,
        )

        assert fmt.format_id == "22"
        assert fmt.ext == "mp4"
        assert fmt.format_note == "720p"
        assert fmt.filesize == 50_000_000

    def test_format_creation_complete(self) -> None:
        """Test Format with all fields."""
        fmt = Format(
            format_id="137",
            ext="mp4",
            format_note="1080p",
            filesize=100_000_000,
            filesize_approx=99_000_000,
            tbr=2500.5,
            vcodec="avc1.640028",
            acodec="none",
            fps=30.0,
            width=1920,
            height=1080,
            resolution="1920x1080",
        )

        assert fmt.format_id == "137"
        assert fmt.tbr == 2500.5
        assert fmt.vcodec == "avc1.640028"
        assert fmt.acodec == "none"
        assert fmt.fps == 30.0
        assert fmt.width == 1920
        assert fmt.height == 1080
        assert fmt.resolution == "1920x1080"

    def test_format_audio_only(self) -> None:
        """Test Format for audio-only stream."""
        fmt = Format(
            format_id="140",
            ext="m4a",
            format_note="audio only",
            filesize=5_000_000,
            acodec="mp4a.40.2",
            tbr=128,
        )

        assert fmt.ext == "m4a"
        assert fmt.acodec == "mp4a.40.2"
        assert fmt.vcodec is None
        assert fmt.width is None
        assert fmt.height is None

    def test_format_factory(self) -> None:
        """Test format factory function from helpers."""
        fmt = make_mock_format("18", "mp4", "640x360", 20_000_000)

        assert fmt.format_id == "18"
        assert fmt.ext == "mp4"
        assert fmt.resolution == "640x360"
        assert fmt.width == 640
        assert fmt.height == 360
        assert fmt.filesize == 20_000_000


class TestTranscription:
    """Tests for Transcription model."""

    def test_transcription_creation(self) -> None:
        """Test creating a basic Transcription model."""
        transcript = Transcription(
            language="en",
            text="Hello, world!",
            auto_generated=False,
            ext="vtt",
        )

        assert transcript.language == "en"
        assert transcript.text == "Hello, world!"
        assert transcript.auto_generated is False
        assert transcript.ext == "vtt"

    def test_transcription_defaults(self) -> None:
        """Test Transcription default values."""
        transcript = Transcription(
            language="es",
            text="Hola, mundo!",
        )

        assert transcript.auto_generated is False
        assert transcript.ext == "vtt"

    def test_transcription_auto_generated(self) -> None:
        """Test auto-generated transcription."""
        transcript = Transcription(
            language="en",
            text="[Auto-generated] Some text",
            auto_generated=True,
            ext="srv3",
        )

        assert transcript.auto_generated is True
        assert transcript.ext == "srv3"

    def test_transcription_factory(self) -> None:
        """Test transcription factory function from helpers."""
        transcript = make_mock_transcription(
            language="fr",
            text="Bonjour le monde!",
            auto_generated=True,
        )

        assert transcript.language == "fr"
        assert transcript.text == "Bonjour le monde!"
        assert transcript.auto_generated is True

    def test_transcription_factory_default_text(self) -> None:
        """Test factory generates default text when not provided."""
        transcript = make_mock_transcription(language="de")

        assert transcript.language == "de"
        assert "manual transcription" in transcript.text
        assert "de" in transcript.text


class TestVideoInfo:
    """Tests for VideoInfo model."""

    def test_video_info_basic(self) -> None:
        """Test creating VideoInfo with required fields."""
        info = VideoInfo(
            url=HttpUrl("https://www.youtube.com/watch?v=test123"),
            id="test123",  # Use alias
            title="Test Video",
        )

        assert info.video_id == "test123"
        assert info.title == "Test Video"
        assert str(info.url) == "https://www.youtube.com/watch?v=test123"

    def test_video_info_complete(self) -> None:
        """Test VideoInfo with all fields populated."""
        now = datetime.now()
        downloaded_file = Path("/tmp/video.mp4")

        info = VideoInfo(
            url=HttpUrl("https://www.youtube.com/watch?v=full123"),
            id="full123",  # Use alias
            title="Full Test Video",
            description="Complete test video with all fields",
            uploader="Test Channel",
            uploader_id="@testchannel",
            channel="Test Channel",
            channel_id="UC_test123",
            upload_date="20231225",
            timestamp=1703462400,
            duration=300,
            view_count=1_000_000,
            like_count=50_000,
            comment_count=1_000,
            age_limit=0,
            is_live=False,
            was_live=False,
            formats=[make_mock_format()],
            thumbnails=[make_mock_thumbnail()],
            categories=["Education", "Technology"],
            tags=["test", "video", "example"],
            downloaded_file=downloaded_file,
            download_timestamp=now,
        )

        assert info.video_id == "full123"
        assert info.description == "Complete test video with all fields"
        assert info.duration == 300
        assert info.view_count == 1_000_000
        assert len(info.formats) == 1
        assert len(info.thumbnails) == 1
        assert "Education" in info.categories
        assert "test" in info.tags
        assert info.downloaded_file == downloaded_file
        assert info.download_timestamp == now

    def test_video_info_alias(self) -> None:
        """Test VideoInfo field alias for 'id' -> 'video_id'."""
        info = VideoInfo.model_validate({
            "url": "https://www.youtube.com/watch?v=alias123",
            "id": "alias123",  # Using alias
            "title": "Alias Test",
        })

        assert info.video_id == "alias123"

    def test_video_info_populate_by_name(self) -> None:
        """Test VideoInfo can be populated by field name or alias."""
        # Using alias 'id' (which maps to video_id)
        info1 = VideoInfo.model_validate({
            "url": "https://www.youtube.com/watch?v=name123",
            "id": "name123",
            "title": "Name Test 1",
        })

        # Also using alias for consistency
        info2 = VideoInfo.model_validate({
            "url": "https://www.youtube.com/watch?v=name123",
            "id": "name123",
            "title": "Name Test 2",
        })

        assert info1.video_id == info2.video_id

    def test_video_info_default_values(self) -> None:
        """Test VideoInfo default values for optional fields."""
        info = VideoInfo(
            url=HttpUrl("https://www.youtube.com/watch?v=defaults"),
            id="defaults",  # Use alias
            title="Default Test",
        )

        assert info.description is None
        assert info.uploader is None
        assert info.duration is None
        assert info.view_count is None
        assert info.age_limit == 0
        assert info.is_live is False
        assert info.was_live is False
        assert info.formats == []
        assert info.thumbnails == []
        assert info.categories == []
        assert info.tags == []
        assert info.downloaded_file is None
        assert info.download_timestamp is None

    def test_video_info_factory(self) -> None:
        """Test video info factory function from helpers."""
        info = make_mock_video_info(
            video_id="factory123",
            title="Factory Test",
            duration=180,
            view_count=500_000,
        )

        assert info.video_id == "factory123"
        assert info.title == "Factory Test"
        assert info.duration == 180
        assert info.view_count == 500_000
        assert len(info.formats) > 0  # Factory includes formats by default
        assert len(info.thumbnails) > 0  # Factory includes thumbnails by default

    def test_video_info_factory_no_formats(self) -> None:
        """Test factory can exclude formats and thumbnails."""
        info = make_mock_video_info(
            include_formats=False,
            include_thumbnails=False,
        )

        assert info.formats == []
        assert info.thumbnails == []

    def test_video_info_extra_ignored(self) -> None:
        """Test VideoInfo ignores extra fields."""
        info = VideoInfo.model_validate({
            "url": "https://www.youtube.com/watch?v=extra",
            "id": "extra",
            "title": "Extra Test",
            "unknown_field": "should be ignored",
            "another_extra": 123,
        })

        assert info.video_id == "extra"
        assert not hasattr(info, "unknown_field")
        assert not hasattr(info, "another_extra")


class TestVideoDownloadOptions:
    """Tests for VideoDownloadOptions dataclass."""

    def test_video_options_defaults(self) -> None:
        """Test VideoDownloadOptions default values."""
        options = VideoDownloadOptions()

        assert options.format == "best"
        assert options.ydl_opts == {}

    def test_video_options_custom(self) -> None:
        """Test VideoDownloadOptions with custom values."""
        custom_opts = {"quiet": True, "no_warnings": True}
        options = VideoDownloadOptions(
            format="bestvideo[height<=720]+bestaudio/best[height<=720]",
            ydl_opts=custom_opts,
        )

        assert options.format == "bestvideo[height<=720]+bestaudio/best[height<=720]"
        assert options.ydl_opts == custom_opts

    def test_video_options_is_dataclass(self) -> None:
        """Test VideoDownloadOptions is a proper dataclass."""
        options = VideoDownloadOptions()

        # Check it has dataclass fields
        dc_fields = fields(options)
        field_names = {f.name for f in dc_fields}

        assert "format" in field_names
        assert "ydl_opts" in field_names


class TestAudioDownloadOptions:
    """Tests for AudioDownloadOptions dataclass."""

    def test_audio_options_defaults(self) -> None:
        """Test AudioDownloadOptions default values."""
        options = AudioDownloadOptions()

        assert options.format == "mp3"
        assert options.quality == "192K"
        assert options.ydl_opts == {}

    def test_audio_options_custom(self) -> None:
        """Test AudioDownloadOptions with custom values."""
        custom_opts = {"prefer_ffmpeg": True}
        options = AudioDownloadOptions(
            format="m4a",
            quality="320K",
            ydl_opts=custom_opts,
        )

        assert options.format == "m4a"
        assert options.quality == "320K"
        assert options.ydl_opts == custom_opts

    def test_audio_options_is_dataclass(self) -> None:
        """Test AudioDownloadOptions is a proper dataclass."""
        options = AudioDownloadOptions()

        # Check it has dataclass fields
        dc_fields = fields(options)
        field_names = {f.name for f in dc_fields}

        assert "format" in field_names
        assert "quality" in field_names
        assert "ydl_opts" in field_names


class TestModelValidation:
    """Test model validation and error handling."""

    def test_format_numeric_fields(self) -> None:
        """Test Format numeric field validation."""
        # Valid numeric values
        fmt = Format(
            format_id="test",
            ext="mp4",
            tbr=1234.56,
            fps=29.97,
            width=1920,
            height=1080,
        )

        assert fmt.tbr == 1234.56
        assert fmt.fps == 29.97

        # Invalid numeric types should raise ValidationError
        with pytest.raises(ValidationError):
            Format(
                format_id="test",
                ext="mp4",
                fps="not a float",  # type: ignore[arg-type]
            )


