"""Tests for Whisper exceptions."""

import pytest

from python.infra.whisper.exceptions import (
    AudioFileError,
    ModelLoadError,
    TranscriptionError,
    WhisperError,
)


def test_whisper_error_base() -> None:
    """Test WhisperError base exception."""
    error = WhisperError("Test error message", "/path/to/file.mp3")

    assert str(error) == "Test error message"
    assert error.message == "Test error message"
    assert error.file_path == "/path/to/file.mp3"
    assert isinstance(error, Exception)


def test_whisper_error_without_file_path() -> None:
    """Test WhisperError without file path."""
    error = WhisperError("Test error message")

    assert error.message == "Test error message"
    assert error.file_path is None


def test_audio_file_error() -> None:
    """Test AudioFileError exception."""
    error = AudioFileError("File not found", "/path/to/missing.mp3")

    assert str(error) == "File not found"
    assert error.message == "File not found"
    assert error.file_path == "/path/to/missing.mp3"
    assert isinstance(error, WhisperError)


def test_transcription_error() -> None:
    """Test TranscriptionError exception."""
    error = TranscriptionError("Transcription failed", "/path/to/audio.mp3")

    assert str(error) == "Transcription failed"
    assert error.message == "Transcription failed"
    assert error.file_path == "/path/to/audio.mp3"
    assert isinstance(error, WhisperError)


def test_model_load_error() -> None:
    """Test ModelLoadError exception."""
    error = ModelLoadError("Failed to load model", "large")

    assert str(error) == "Failed to load model"
    assert error.message == "Failed to load model"
    assert error.model_name == "large"
    assert error.file_path is None
    assert isinstance(error, WhisperError)


def test_model_load_error_without_model_name() -> None:
    """Test ModelLoadError without model name."""
    error = ModelLoadError("Failed to load model")

    assert error.message == "Failed to load model"
    assert error.model_name is None


def test_exception_inheritance() -> None:
    """Test that all custom exceptions inherit from WhisperError."""
    assert issubclass(AudioFileError, WhisperError)
    assert issubclass(TranscriptionError, WhisperError)
    assert issubclass(ModelLoadError, WhisperError)


def test_exception_can_be_raised() -> None:
    """Test that exceptions can be raised and caught."""
    with pytest.raises(AudioFileError) as exc_info:
        raise AudioFileError("Test error", "/test/path.mp3")

    assert exc_info.value.message == "Test error"
    assert exc_info.value.file_path == "/test/path.mp3"


def test_catch_base_exception() -> None:
    """Test that WhisperError can catch all custom exceptions."""
    with pytest.raises(WhisperError):
        raise AudioFileError("Test error")

    with pytest.raises(WhisperError):
        raise TranscriptionError("Test error")

    with pytest.raises(WhisperError):
        raise ModelLoadError("Test error")
