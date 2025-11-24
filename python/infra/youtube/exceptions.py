"""Custom exceptions for YouTube operations."""


class YouTubeError(Exception):
    """Base exception for all YouTube-related errors."""

    def __init__(self, message: str, url: str | None = None) -> None:
        self.message = message
        self.url = url
        super().__init__(message)


class InvalidURLError(YouTubeError):
    """Raised when YouTube URL is invalid or unsupported."""


class ExtractionError(YouTubeError):
    """Raised when metadata extraction fails."""


class DownloadError(YouTubeError):
    """Raised when video/audio download fails."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        partial_file: str | None = None,
    ) -> None:
        super().__init__(message, url)
        self.partial_file = partial_file


class TranscriptionError(YouTubeError):
    """Raised when subtitle/transcription extraction fails."""


class UnavailableVideoError(YouTubeError):
    """Raised when video is unavailable (private, deleted, geo-blocked, etc.)."""
