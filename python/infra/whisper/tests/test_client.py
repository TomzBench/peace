"""Tests for Whisper client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from python.infra.whisper.client import (
    MAX_FILE_SIZE_BYTES,
    _get_client,
    _validate_audio_file,
    transcribe_audio,
)
from python.infra.whisper.exceptions import (
    AudioFileError,
    TranscriptionError,
    WhisperError,
)
from python.infra.whisper.models import (
    TranscriptionOptions,
    TranscriptionResult,
)

# Test _get_client()


@patch("python.infra.whisper.client.get_settings")
@patch("python.infra.whisper.client.OpenAI")
def test_get_client_success(mock_openai: Mock, mock_settings: Mock) -> None:
    """Test getting OpenAI client with valid API key."""
    mock_settings.return_value.openai_api_key = "test-api-key"
    mock_settings.return_value.openai_organization = "test-org"

    client = _get_client()

    mock_openai.assert_called_once_with(
        api_key="test-api-key",
        organization="test-org",
    )
    assert client is not None


@patch("python.infra.whisper.client.get_settings")
def test_get_client_missing_api_key(mock_settings: Mock) -> None:
    """Test that missing API key raises WhisperError."""
    mock_settings.return_value.openai_api_key = None

    with pytest.raises(WhisperError) as exc_info:
        _get_client()

    assert "OpenAI API key not configured" in str(exc_info.value)


# Test _validate_audio_file()


def test_validate_audio_file_success(tmp_path: Path) -> None:
    """Test validation of valid audio file."""
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Should not raise
    _validate_audio_file(audio_file)


def test_validate_audio_file_not_found() -> None:
    """Test validation fails for non-existent file."""
    audio_file = Path("/nonexistent/file.mp3")

    with pytest.raises(AudioFileError) as exc_info:
        _validate_audio_file(audio_file)

    assert "Audio file not found" in str(exc_info.value)
    assert exc_info.value.file_path == str(audio_file)


def test_validate_audio_file_is_directory(tmp_path: Path) -> None:
    """Test validation fails for directory."""
    audio_dir = tmp_path / "audio_dir"
    audio_dir.mkdir()

    with pytest.raises(AudioFileError) as exc_info:
        _validate_audio_file(audio_dir)

    assert "Path is not a file" in str(exc_info.value)


def test_validate_audio_file_exceeds_size_limit(tmp_path: Path) -> None:
    """Test validation fails for file exceeding 25MB limit."""
    audio_file = tmp_path / "large.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Mock the file size check to return size > 25MB
    with patch.object(Path, "stat") as mock_stat:

        # Create a mock stat result with proper st_mode for is_file() and large st_size
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = 0o100644  # Regular file mode
        mock_stat_result.st_size = MAX_FILE_SIZE_BYTES + 1
        mock_stat.return_value = mock_stat_result

        with pytest.raises(AudioFileError) as exc_info:
            _validate_audio_file(audio_file)

        assert "exceeds" in str(exc_info.value)
        assert "25MB" in str(exc_info.value)


def test_validate_audio_file_unusual_extension(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test validation warns for unusual file extension."""
    audio_file = tmp_path / "test.xyz"
    audio_file.write_bytes(b"fake audio data")

    _validate_audio_file(audio_file)

    assert "unusual extension" in caplog.text


# Test transcribe_audio()


@patch("python.infra.whisper.client._get_client")
@patch("python.infra.whisper.client._validate_audio_file")
def test_transcribe_audio_success(
    mock_validate: Mock,
    mock_get_client: Mock,
    tmp_path: Path,
) -> None:
    """Test successful transcription with basic options."""
    # Setup
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Mock OpenAI client response
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = "Transcribed text"
    mock_response.language = "en"
    mock_response.duration = 10.5
    mock_response.segments = [
        {
            "id": 0,
            "seek": 0,
            "start": 0.0,
            "end": 5.0,
            "text": "First segment",
            "tokens": [1, 2, 3],
            "temperature": 0.0,
            "avg_logprob": -0.2,
            "compression_ratio": 1.5,
            "no_speech_prob": 0.01,
        },
    ]
    mock_response.usage = None

    mock_client.audio.transcriptions.create.return_value = mock_response

    # Execute
    result = transcribe_audio(audio_file)

    # Verify
    assert isinstance(result, TranscriptionResult)
    assert result.text == "Transcribed text"
    assert result.language == "en"
    assert result.duration == 10.5
    assert len(result.segments) == 1
    assert result.segments[0].text == "First segment"
    assert result.audio_file == audio_file
    assert result.model_name == "whisper-1"
    assert result.usage is None

    # Verify API was called with correct params
    mock_client.audio.transcriptions.create.assert_called_once()
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-1"
    assert call_kwargs["response_format"] == "verbose_json"


@patch("python.infra.whisper.client._get_client")
@patch("python.infra.whisper.client._validate_audio_file")
def test_transcribe_audio_with_custom_options(
    mock_validate: Mock,
    mock_get_client: Mock,
    tmp_path: Path,
) -> None:
    """Test transcription with custom options."""
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = "Custom transcription"
    mock_response.language = "es"
    mock_response.duration = 15.0
    mock_response.segments = []
    mock_response.usage = None

    mock_client.audio.transcriptions.create.return_value = mock_response

    # Custom options
    options = TranscriptionOptions(
        model="gpt-4o-transcribe",
        language="es",
        temperature=0.3,
        prompt="Custom prompt",
    )

    result = transcribe_audio(audio_file, options)

    assert result.text == "Custom transcription"
    assert result.language == "es"
    assert result.model_name == "gpt-4o-transcribe"

    # Verify custom options were passed to API
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o-transcribe"
    assert call_kwargs["language"] == "es"
    assert call_kwargs["temperature"] == 0.3
    assert call_kwargs["prompt"] == "Custom prompt"
    assert call_kwargs["response_format"] == "verbose_json"  # Always forced


@patch("python.infra.whisper.client._get_client")
@patch("python.infra.whisper.client._validate_audio_file")
def test_transcribe_audio_with_usage_data(
    mock_validate: Mock,
    mock_get_client: Mock,
    tmp_path: Path,
) -> None:
    """Test transcription with SDK usage data (UsageDuration)."""
    from openai.types.audio.transcription import UsageDuration

    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Mock response with SDK UsageDuration
    usage = UsageDuration(type="duration", seconds=120.5)

    mock_response = MagicMock()
    mock_response.text = "Text"
    mock_response.language = "en"
    mock_response.duration = 120.5
    mock_response.segments = []
    mock_response.usage = usage

    mock_client.audio.transcriptions.create.return_value = mock_response

    result = transcribe_audio(audio_file)

    assert result.usage is not None
    assert result.usage.type == "duration"
    assert result.usage.seconds == 120.5


@patch("python.infra.whisper.client._get_client")
@patch("python.infra.whisper.client._validate_audio_file")
def test_transcribe_audio_with_token_usage(
    mock_validate: Mock,
    mock_get_client: Mock,
    tmp_path: Path,
) -> None:
    """Test transcription with SDK token-based usage data (UsageTokens)."""
    from openai.types.audio.transcription import UsageTokens

    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Mock response with SDK UsageTokens
    usage = UsageTokens(
        type="tokens",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
    )

    mock_response = MagicMock()
    mock_response.text = "Text"
    mock_response.language = "en"
    mock_response.duration = 10.0
    mock_response.segments = []
    mock_response.usage = usage

    mock_client.audio.transcriptions.create.return_value = mock_response

    result = transcribe_audio(audio_file)

    assert result.usage is not None
    assert result.usage.type == "tokens"
    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 50
    assert result.usage.total_tokens == 150


@patch("python.infra.whisper.client._get_client")
def test_transcribe_audio_validation_failure(
    mock_get_client: Mock,
) -> None:
    """Test that audio validation errors are propagated."""
    audio_file = Path("/nonexistent/file.mp3")

    with pytest.raises(AudioFileError) as exc_info:
        transcribe_audio(audio_file)

    assert "Audio file not found" in str(exc_info.value)


@patch("python.infra.whisper.client.get_settings")
@patch("python.infra.whisper.client._validate_audio_file")
def test_transcribe_audio_api_key_error(
    mock_validate: Mock,
    mock_settings: Mock,
    tmp_path: Path,
) -> None:
    """Test that missing API key errors are propagated."""
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    mock_settings.return_value.openai_api_key = None

    with pytest.raises(WhisperError) as exc_info:
        transcribe_audio(audio_file)

    assert "OpenAI API key not configured" in str(exc_info.value)


@patch("python.infra.whisper.client._get_client")
@patch("python.infra.whisper.client._validate_audio_file")
def test_transcribe_audio_api_failure(
    mock_validate: Mock,
    mock_get_client: Mock,
    tmp_path: Path,
) -> None:
    """Test that API failures are wrapped in TranscriptionError."""
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Simulate API error
    mock_client.audio.transcriptions.create.side_effect = Exception("API error")

    with pytest.raises(TranscriptionError) as exc_info:
        transcribe_audio(audio_file)

    assert "API transcription failed" in str(exc_info.value)
    assert "API error" in str(exc_info.value)
    assert exc_info.value.file_path == str(audio_file)


@patch("python.infra.whisper.client._get_client")
@patch("python.infra.whisper.client._validate_audio_file")
def test_transcribe_audio_pydantic_validation(
    mock_validate: Mock,
    mock_get_client: Mock,
    tmp_path: Path,
) -> None:
    """Test that Pydantic validates response data including segments."""
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"fake audio data")

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Response with valid segment structure
    mock_response = MagicMock()
    mock_response.text = "Test"
    mock_response.language = "en"
    mock_response.duration = 5.0
    mock_response.segments = [
        {
            "id": 0,
            "seek": 0,
            "start": 0.0,
            "end": 5.0,
            "text": "Valid segment",
            "tokens": [1, 2],
            "temperature": 0.0,
            "avg_logprob": -0.1,
            "compression_ratio": 1.0,
            "no_speech_prob": 0.0,
        },
    ]
    mock_response.usage = None

    mock_client.audio.transcriptions.create.return_value = mock_response

    result = transcribe_audio(audio_file)

    # Pydantic should have validated and converted segments to Segment models
    assert len(result.segments) == 1
    assert result.segments[0].id == 0
    assert result.segments[0].text == "Valid segment"
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 5.0
