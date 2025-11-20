"""Custom exceptions for YouTube operations."""


class YouTubeError(Exception):
    """Base exception for all YouTube-related errors."""

    def __init__(self, message: str, url: str | None = None) -> None:
        """Initialize YouTube error.

        Args:
            message: Error description
            url: YouTube URL that caused the error (if applicable)
        """
        self.message = message
        self.url = url
        super().__init__(message)


class InvalidURLError(YouTubeError):
    """Raised when YouTube URL is invalid or unsupported."""

    pass


class ExtractionError(YouTubeError):
    """Raised when metadata extraction fails."""

    pass


class DownloadError(YouTubeError):
    """Raised when video/audio download fails."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        partial_file: str | None = None,
    ) -> None:
        """Initialize download error.

        Args:
            message: Error description
            url: YouTube URL that failed
            partial_file: Path to partial download (if any)
        """
        super().__init__(message, url)
        self.partial_file = partial_file


class TranscriptionError(YouTubeError):
    """Raised when subtitle/transcription extraction fails."""

    pass


class UnavailableVideoError(YouTubeError):
    """Raised when video is unavailable (private, deleted, geo-blocked, etc.)."""

    pass
