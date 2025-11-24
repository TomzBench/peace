"""Tests for YouTube exceptions.

This module tests all custom exception classes in the YouTube module,
ensuring proper inheritance, attributes, and error messages.
"""

import pytest

from python.infra.youtube.exceptions import (
    DownloadError,
    ExtractionError,
    InvalidURLError,
    TranscriptionError,
    UnavailableVideoError,
    YouTubeError,
)


class TestYouTubeError:
    """Tests for base YouTubeError exception."""

    def test_youtube_error_basic(self) -> None:
        """Test creating basic YouTubeError."""
        error = YouTubeError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.url is None

    def test_youtube_error_with_url(self) -> None:
        """Test YouTubeError with URL."""
        url = "https://www.youtube.com/watch?v=test123"
        error = YouTubeError("Failed to process video", url=url)

        assert error.message == "Failed to process video"
        assert error.url == url
        assert str(error) == "Failed to process video"


    def test_youtube_error_raise_and_catch(self) -> None:
        """Test raising and catching YouTubeError."""
        with pytest.raises(YouTubeError) as exc_info:
            raise YouTubeError("Test exception", url="https://youtube.com/test")

        assert exc_info.value.message == "Test exception"
        assert exc_info.value.url == "https://youtube.com/test"


class TestInvalidURLError:
    """Tests for InvalidURLError exception."""

    def test_invalid_url_error_basic(self) -> None:
        """Test creating InvalidURLError."""
        error = InvalidURLError("Not a valid YouTube URL")

        assert error.message == "Not a valid YouTube URL"
        assert isinstance(error, YouTubeError)
        assert isinstance(error, InvalidURLError)

    def test_invalid_url_error_with_url(self) -> None:
        """Test InvalidURLError with the invalid URL."""
        bad_url = "https://not-youtube.com/video"
        error = InvalidURLError("Invalid domain", url=bad_url)

        assert error.message == "Invalid domain"
        assert error.url == bad_url

    def test_invalid_url_error_in_exception_chain(self) -> None:
        """Test InvalidURLError in exception handling."""
        def process_url(url: str) -> None:
            if "youtube.com" not in url and "youtu.be" not in url:
                raise InvalidURLError(f"URL must be from YouTube: {url}", url=url)

        with pytest.raises(InvalidURLError) as exc_info:
            process_url("https://vimeo.com/123")

        assert "must be from YouTube" in exc_info.value.message
        assert exc_info.value.url == "https://vimeo.com/123"


class TestExtractionError:
    """Tests for ExtractionError exception."""

    def test_extraction_error_basic(self) -> None:
        """Test creating ExtractionError."""
        error = ExtractionError("Failed to extract video metadata")

        assert error.message == "Failed to extract video metadata"
        assert isinstance(error, YouTubeError)
        assert isinstance(error, ExtractionError)

    def test_extraction_error_with_details(self) -> None:
        """Test ExtractionError with detailed message and URL."""
        url = "https://www.youtube.com/watch?v=abc123"
        error = ExtractionError(
            "Unable to parse video info: missing 'title' field",
            url=url,
        )

        assert "missing 'title' field" in error.message
        assert error.url == url

    def test_extraction_error_from_parsing(self) -> None:
        """Test ExtractionError raised during parsing."""
        def parse_video_data(data: dict) -> None:
            if "id" not in data:
                raise ExtractionError("Video ID not found in response data")

        with pytest.raises(ExtractionError) as exc_info:
            parse_video_data({})

        assert "Video ID not found" in str(exc_info.value)


class TestDownloadError:
    """Tests for DownloadError exception."""

    def test_download_error_basic(self) -> None:
        """Test creating basic DownloadError."""
        error = DownloadError("Download failed")

        assert error.message == "Download failed"
        assert error.url is None
        assert error.partial_file is None
        assert isinstance(error, YouTubeError)
        assert isinstance(error, DownloadError)

    def test_download_error_with_url(self) -> None:
        """Test DownloadError with URL."""
        url = "https://www.youtube.com/watch?v=xyz789"
        error = DownloadError("Network timeout", url=url)

        assert error.message == "Network timeout"
        assert error.url == url
        assert error.partial_file is None

    def test_download_error_with_partial_file(self) -> None:
        """Test DownloadError with partial file path."""
        url = "https://www.youtube.com/watch?v=partial123"
        partial_path = "/tmp/downloads/video.mp4.part"
        error = DownloadError(
            "Download interrupted at 45%",
            url=url,
            partial_file=partial_path,
        )

        assert error.message == "Download interrupted at 45%"
        assert error.url == url
        assert error.partial_file == partial_path

    def test_download_error_complete_info(self) -> None:
        """Test DownloadError with all attributes."""
        error = DownloadError(
            message="Connection lost during download",
            url="https://youtube.com/watch?v=test",
            partial_file="/tmp/test.mp4.part",
        )

        assert error.message == "Connection lost during download"
        assert error.url == "https://youtube.com/watch?v=test"
        assert error.partial_file == "/tmp/test.mp4.part"



class TestTranscriptionError:
    """Tests for TranscriptionError exception."""

    def test_transcription_error_basic(self) -> None:
        """Test creating TranscriptionError."""
        error = TranscriptionError("No subtitles available")

        assert error.message == "No subtitles available"
        assert isinstance(error, YouTubeError)
        assert isinstance(error, TranscriptionError)

    def test_transcription_error_with_language(self) -> None:
        """Test TranscriptionError for specific language."""
        url = "https://www.youtube.com/watch?v=nosubs"
        error = TranscriptionError(
            "No English (en) subtitles found",
            url=url,
        )

        assert "English (en)" in error.message
        assert error.url == url

    def test_transcription_error_auto_captions(self) -> None:
        """Test TranscriptionError for auto-caption issues."""
        error = TranscriptionError(
            "Auto-generated captions are disabled for this video",
            url="https://youtube.com/watch?v=noauto",
        )

        assert "Auto-generated captions" in error.message
        assert error.url == "https://youtube.com/watch?v=noauto"



class TestUnavailableVideoError:
    """Tests for UnavailableVideoError exception."""

    def test_unavailable_video_error_basic(self) -> None:
        """Test creating UnavailableVideoError."""
        error = UnavailableVideoError("Video is private")

        assert error.message == "Video is private"
        assert isinstance(error, YouTubeError)
        assert isinstance(error, UnavailableVideoError)

    def test_unavailable_video_error_deleted(self) -> None:
        """Test UnavailableVideoError for deleted video."""
        url = "https://www.youtube.com/watch?v=deleted123"
        error = UnavailableVideoError(
            "This video has been removed by the uploader",
            url=url,
        )

        assert "removed by the uploader" in error.message
        assert error.url == url

    def test_unavailable_video_error_geo_blocked(self) -> None:
        """Test UnavailableVideoError for geo-blocked content."""
        error = UnavailableVideoError(
            "This video is not available in your country",
            url="https://youtube.com/watch?v=geoblocked",
        )

        assert "not available in your country" in error.message

    def test_unavailable_video_error_age_restricted(self) -> None:
        """Test UnavailableVideoError for age-restricted content."""
        error = UnavailableVideoError(
            "Sign in to confirm your age",
            url="https://youtube.com/watch?v=mature",
        )

        assert "Sign in" in error.message
        assert "age" in error.message

    def test_unavailable_video_error_types(self) -> None:
        """Test different types of video unavailability."""
        # Test just two common cases
        error1 = UnavailableVideoError("Video is private")
        assert error1.message == "Video is private"

        error2 = UnavailableVideoError("Video has been removed")
        assert error2.message == "Video has been removed"


class TestExceptionHierarchy:
    """Test the exception hierarchy and relationships."""


    def test_catching_base_exception(self) -> None:
        """Test catching base YouTubeError catches all subtypes."""
        exceptions = [
            InvalidURLError("Invalid URL"),
            ExtractionError("Extraction failed"),
            DownloadError("Download failed"),
            TranscriptionError("No transcription"),
            UnavailableVideoError("Video unavailable"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except YouTubeError as e:
                assert e.message in [
                    "Invalid URL",
                    "Extraction failed",
                    "Download failed",
                    "No transcription",
                    "Video unavailable",
                ]

    def test_specific_exception_handling(self) -> None:
        """Test handling specific exception types."""
        def process_video(error_type: str) -> None:
            if error_type == "url":
                raise InvalidURLError("Bad URL")
            elif error_type == "download":
                raise DownloadError("Download failed")
            elif error_type == "unavailable":
                raise UnavailableVideoError("Video deleted")

        # Test catching specific exceptions
        with pytest.raises(InvalidURLError):
            process_video("url")

        with pytest.raises(DownloadError):
            process_video("download")

        with pytest.raises(UnavailableVideoError):
            process_video("unavailable")

