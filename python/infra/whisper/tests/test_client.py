"""Tests for Whisper client functions."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from python.infra.whisper.client import (
    MAX_FILE_SIZE_BYTES,
    _get_client,
    _parse_segments,
    _validate_audio_file,
    transcribe_and_translate,
    transcribe_audio,
)
from python.infra.whisper.exceptions import (
    AudioFileError,
    TranscriptionError,
    WhisperError,
)
from python.infra.whisper.models import TranscriptionApiOptions


def test_validate_audio_file_exists(temp_audio_file: Path) -> None:
    """Test validating an existing audio file."""
    # Should not raise any exception
    _validate_audio_file(temp_audio_file)


def test_validate_audio_file_missing(invalid_audio_file: Path) -> None:
    """Test validating a missing audio file."""
    with pytest.raises(AudioFileError) as exc_info:
        _validate_audio_file(invalid_audio_file)

    assert "not found" in str(exc_info.value).lower()
    assert exc_info.value.file_path == str(invalid_audio_file)


def test_validate_audio_file_is_directory(tmp_path: Path) -> None:
    """Test validating a directory instead of file."""
    directory = tmp_path / "test_dir"
    directory.mkdir()

    with pytest.raises(AudioFileError) as exc_info:
        _validate_audio_file(directory)

    assert "not a file" in str(exc_info.value).lower()


def test_validate_audio_file_size_limit(tmp_path: Path) -> None:
    """Test validating file size doesn't exceed 25MB API limit."""
    large_file = tmp_path / "large_audio.mp3"
    # Create a file larger than 25MB
    large_file.write_bytes(b"x" * (MAX_FILE_SIZE_BYTES + 1))

    with pytest.raises(AudioFileError) as exc_info:
        _validate_audio_file(large_file)

    assert "25mb" in str(exc_info.value).lower()
    assert "exceeds" in str(exc_info.value).lower()


def test_parse_segments(mock_whisper_result: dict[str, Any]) -> None:
    """Test parsing Whisper segments into Segment models."""
    segments = _parse_segments(mock_whisper_result["segments"])

    assert len(segments) == 2

    # Check first segment
    assert segments[0].id == 0
    assert segments[0].start == 0.0
    assert segments[0].end == 2.5
    assert segments[0].text == "Hello, this is a test"
    assert segments[0].tokens == [1, 2, 3, 4, 5]
    assert segments[0].temperature == 0.0
    assert segments[0].avg_logprob == -0.25
    assert segments[0].compression_ratio == 1.5
    assert segments[0].no_speech_prob == 0.01

    # Check second segment
    assert segments[1].id == 1
    assert segments[1].start == 2.5
    assert segments[1].end == 4.0
    assert segments[1].text == " transcription."


def test_parse_segments_empty() -> None:
    """Test parsing empty segment list."""
    segments = _parse_segments([])
    assert segments == []


def test_parse_segments_with_invalid_data() -> None:
    """Test parsing segments with some invalid data."""
    segments_data: list[dict[str, Any]] = [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.0,
            "text": "Valid segment",
            "tokens": [1, 2],
            "temperature": 0.0,
            "avg_logprob": -0.2,
            "compression_ratio": 1.5,
            "no_speech_prob": 0.01,
        },
        # Invalid segment - missing required fields
        {"id": 1, "start": 2.0},
    ]

    segments = _parse_segments(segments_data)

    # Should only parse the valid segment, skip invalid
    assert len(segments) == 1
    assert segments[0].text == "Valid segment"


@patch("python.infra.whisper.client.get_settings")
def test_get_client_success(mock_get_settings: MagicMock) -> None:
    """Test getting OpenAI client with valid API key."""
    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test-key"
    mock_settings.openai_organization = None
    mock_get_settings.return_value = mock_settings

    client = _get_client()

    assert client is not None
    # Client should be an OpenAI instance
    from openai import OpenAI

    assert isinstance(client, OpenAI)


@patch("python.infra.whisper.client.get_settings")
def test_get_client_missing_api_key(mock_get_settings: MagicMock) -> None:
    """Test that missing API key raises WhisperError."""
    mock_settings = MagicMock()
    mock_settings.openai_api_key = None
    mock_get_settings.return_value = mock_settings

    with pytest.raises(WhisperError) as exc_info:
        _get_client()

    assert "api key not configured" in str(exc_info.value).lower()


@patch("python.infra.whisper.client.get_settings")
def test_get_client_with_organization(mock_get_settings: MagicMock) -> None:
    """Test getting OpenAI client with organization."""
    mock_settings = MagicMock()
    mock_settings.openai_api_key = "sk-test-key"
    mock_settings.openai_organization = "org-test"
    mock_get_settings.return_value = mock_settings

    client = _get_client()

    assert client is not None
    from openai import OpenAI

    assert isinstance(client, OpenAI)


@patch("python.infra.whisper.client._get_client")
def test_transcribe_audio(
    mock_get_client: MagicMock,
    temp_audio_file: Path,
    mock_whisper_result: dict[str, Any],
) -> None:
    """Test transcribing an audio file via API."""
    # Setup mock client and response
    mock_client = MagicMock()
    mock_response = Mock()
    mock_response.text = mock_whisper_result["text"]
    mock_response.segments = mock_whisper_result["segments"]
    mock_response.language = mock_whisper_result["language"]
    mock_response.duration = mock_whisper_result["duration"]

    mock_client.audio.transcriptions.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    # Transcribe
    result = transcribe_audio(temp_audio_file)

    # Verify result
    assert result.text == "Hello, this is a test transcription."
    assert len(result.segments) == 2
    assert result.language == "en"
    assert result.audio_file == temp_audio_file
    assert result.model_name == "whisper-1"
    assert result.duration == 4.0

    # Verify API was called correctly
    mock_client.audio.transcriptions.create.assert_called_once()
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-1"
    assert call_kwargs["response_format"] == "verbose_json"


@patch("python.infra.whisper.client._get_client")
def test_transcribe_audio_with_options(
    mock_get_client: MagicMock,
    temp_audio_file: Path,
    mock_whisper_result: dict[str, Any],
) -> None:
    """Test transcribing with custom options."""
    # Setup mock client and response
    mock_client = MagicMock()
    mock_response = Mock()
    mock_response.text = mock_whisper_result["text"]
    mock_response.segments = mock_whisper_result["segments"]
    mock_response.language = mock_whisper_result["language"]
    mock_response.duration = mock_whisper_result["duration"]

    mock_client.audio.transcriptions.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    # Transcribe with options
    options = TranscriptionApiOptions(
        language="en",
        temperature=0.5,
        initial_prompt="This is a test",
    )
    result = transcribe_audio(temp_audio_file, options)

    # Verify result - API always uses whisper-1 model
    assert result.model_name == "whisper-1"

    # Verify API was called with correct parameters
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["language"] == "en"
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["prompt"] == "This is a test"  # Note: renamed to "prompt"


def test_transcribe_audio_file_not_found(
    invalid_audio_file: Path,
) -> None:
    """Test transcribing a missing audio file."""
    with pytest.raises(AudioFileError):
        transcribe_audio(invalid_audio_file)


@patch("python.infra.whisper.client._get_client")
def test_transcribe_audio_api_key_error(
    mock_get_client: MagicMock,
    temp_audio_file: Path,
) -> None:
    """Test transcription when API key is missing."""
    mock_get_client.side_effect = WhisperError("API key not configured")

    with pytest.raises(WhisperError):
        transcribe_audio(temp_audio_file)


@patch("python.infra.whisper.client._get_client")
def test_transcribe_audio_transcription_error(
    mock_get_client: MagicMock,
    temp_audio_file: Path,
) -> None:
    """Test API transcription failure."""
    # Setup mock to raise exception
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.side_effect = Exception("API error")
    mock_get_client.return_value = mock_client

    with pytest.raises(TranscriptionError) as exc_info:
        transcribe_audio(temp_audio_file)

    assert "api" in str(exc_info.value).lower()


@patch("python.infra.whisper.client._get_client")
def test_transcribe_and_translate(
    mock_get_client: MagicMock,
    temp_audio_file: Path,
    mock_translated_result: dict[str, Any],
) -> None:
    """Test transcribing and translating to English via API."""
    # Setup mock client and response
    mock_client = MagicMock()
    mock_response = Mock()
    mock_response.text = mock_translated_result["text"]
    mock_response.segments = mock_translated_result["segments"]
    mock_response.language = mock_translated_result["language"]
    mock_response.duration = mock_translated_result["duration"]

    mock_client.audio.translations.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    # Transcribe and translate
    result = transcribe_and_translate(temp_audio_file)

    # Verify result
    assert result.text == "Hello, this is an English translation."
    assert result.translation == "Hello, this is an English translation."
    assert result.language == "es"  # Original language

    # Verify translations endpoint was called (not transcriptions)
    mock_client.audio.translations.create.assert_called_once()


@patch("python.infra.whisper.client._get_client")
def test_transcribe_and_translate_with_options(
    mock_get_client: MagicMock,
    temp_audio_file: Path,
    mock_translated_result: dict[str, Any],
) -> None:
    """Test transcribe_and_translate with options."""
    # Setup mock client and response
    mock_client = MagicMock()
    mock_response = Mock()
    mock_response.text = mock_translated_result["text"]
    mock_response.segments = mock_translated_result["segments"]
    mock_response.language = mock_translated_result["language"]
    mock_response.duration = mock_translated_result["duration"]

    mock_client.audio.translations.create.return_value = mock_response
    mock_get_client.return_value = mock_client

    # Use API options - translation endpoint handles language detection automatically
    options = TranscriptionApiOptions(temperature=0.3)
    result = transcribe_and_translate(temp_audio_file, options)

    # Verify translations endpoint was used
    mock_client.audio.translations.create.assert_called_once()
    assert result.translation is not None  # Ensure translation field is set
