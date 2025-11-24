"""Custom exceptions for Whisper transcription operations."""


class WhisperError(Exception):
    """Base exception for all Whisper-related errors."""

    def __init__(self, message: str, file_path: str | None = None) -> None:
        self.message = message
        self.file_path = file_path
        super().__init__(message)


class AudioFileError(WhisperError):
    """Raised when audio file is invalid, missing, or unsupported."""


class TranscriptionError(WhisperError):
    """Raised when transcription process fails."""


class ModelLoadError(WhisperError):
    """Raised when Whisper model fails to load."""

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
    ) -> None:
        super().__init__(message, file_path=None)
        self.model_name = model_name
