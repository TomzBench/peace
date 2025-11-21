"""Tests for Whisper client."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from python.infra.whisper.client import transcribe_audio
from python.infra.whisper.exceptions import TranscriptionError
from python.infra.whisper.models import AudioFile, TranscriptionOptions, TranscriptionResult

# Tests for client creation moved to test_dependencies.py


def test_transcribe_audio_success() -> None:
    """Test successful transcription with basic options."""
    # Create AudioFile
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock OpenAI client response
    mock_client = MagicMock()
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

    # Execute - use explicit client injection
    result = transcribe_audio(audio_file, client=mock_client)

    # Verify
    assert isinstance(result, TranscriptionResult)
    assert result.text == "Transcribed text"
    assert result.language == "en"
    assert result.duration == 10.5
    assert len(result.segments) == 1
    assert result.segments[0].text == "First segment"
    assert result.audio_file == audio_file.path
    assert result.model_name == "whisper-1"
    assert result.usage is None

    # Verify API was called with correct params
    mock_client.audio.transcriptions.create.assert_called_once()
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-1"
    assert call_kwargs["response_format"] == "verbose_json"


def test_transcribe_audio_with_custom_options() -> None:
    """Test transcription with custom options."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    mock_client = MagicMock()
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

    result = transcribe_audio(audio_file, options, client=mock_client)

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


def test_transcribe_audio_with_usage_data() -> None:
    """Test transcription with SDK usage data (UsageDuration)."""
    from openai.types.audio.transcription import UsageDuration

    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    mock_client = MagicMock()

    # Mock response with SDK UsageDuration
    usage = UsageDuration(type="duration", seconds=120.5)

    mock_response = MagicMock()
    mock_response.text = "Text"
    mock_response.language = "en"
    mock_response.duration = 120.5
    mock_response.segments = []
    mock_response.usage = usage

    mock_client.audio.transcriptions.create.return_value = mock_response

    result = transcribe_audio(audio_file, client=mock_client)

    assert result.usage is not None
    assert result.usage.type == "duration"
    assert result.usage.seconds == 120.5


def test_transcribe_audio_with_token_usage() -> None:
    """Test transcription with SDK token-based usage data (UsageTokens)."""
    from openai.types.audio.transcription import UsageTokens

    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    mock_client = MagicMock()

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

    result = transcribe_audio(audio_file, client=mock_client)

    assert result.usage is not None
    assert result.usage.type == "tokens"
    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 50
    assert result.usage.total_tokens == 150


@patch("python.infra.whisper.dependencies.get_settings")
def test_transcribe_audio_api_key_error(
    mock_settings: Mock,
) -> None:
    """Test that missing API key raises OpenAIError during dependency injection."""
    from openai import OpenAIError

    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    mock_settings.return_value.openai_api_key = None

    # DI layer propagates OpenAI SDK errors directly
    with pytest.raises(OpenAIError) as exc_info:
        transcribe_audio(audio_file)  # Will try to get client via DI

    assert "api_key" in str(exc_info.value).lower()


def test_transcribe_audio_api_failure() -> None:
    """Test that API failures are wrapped in TranscriptionError."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    mock_client = MagicMock()

    # Simulate API error
    mock_client.audio.transcriptions.create.side_effect = Exception("API error")

    with pytest.raises(TranscriptionError) as exc_info:
        transcribe_audio(audio_file, client=mock_client)

    assert "API transcription failed" in str(exc_info.value)
    assert "API error" in str(exc_info.value)
    assert exc_info.value.file_path == str(audio_file.path)


def test_transcribe_audio_pydantic_validation() -> None:
    """Test that Pydantic validates response data including segments."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    mock_client = MagicMock()

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

    result = transcribe_audio(audio_file, client=mock_client)

    # Pydantic should have validated and converted segments to Segment models
    assert len(result.segments) == 1
    assert result.segments[0].id == 0
    assert result.segments[0].text == "Valid segment"
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 5.0


# Test new dependency override pattern


def test_transcribe_audio_with_dependency_override() -> None:
    """Test using new override_dependency pattern for cleaner testing."""
    from python.infra.whisper.dependencies import override_dependency

    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create mock client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Dependency override test"
    mock_response.language = "en"
    mock_response.duration = 5.0
    mock_response.segments = []
    mock_response.usage = None
    mock_client.audio.transcriptions.create.return_value = mock_response

    # Use override_dependency context manager
    with override_dependency("client", lambda: mock_client):
        result = transcribe_audio(audio_file)

    assert result.text == "Dependency override test"
    assert result.language == "en"
    mock_client.audio.transcriptions.create.assert_called_once()


def test_transcribe_audio_with_explicit_client_injection() -> None:
    """Test explicitly passing client parameter (bypasses DI)."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create mock client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Explicit injection test"
    mock_response.language = "es"
    mock_response.duration = 8.0
    mock_response.segments = []
    mock_response.usage = None
    mock_client.audio.transcriptions.create.return_value = mock_response

    # Explicitly pass client - no DI needed
    result = transcribe_audio(audio_file, client=mock_client)

    assert result.text == "Explicit injection test"
    assert result.language == "es"
    mock_client.audio.transcriptions.create.assert_called_once()
