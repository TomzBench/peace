"""Tests for Whisper client."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from python.infra.whisper.client import transcribe_audio
from python.infra.whisper.exceptions import TranscriptionError
from python.infra.whisper.models import (
    AudioFile,
    AudioFileChunk,
    TranscriptionOptions,
    TranscriptionResult,
    TranscriptionSegment,
)

# Tests for client creation moved to test_dependencies.py


# Test Assertion Helpers


def assert_transcription_result_ok(
    result: TranscriptionResult,
    expected_text: str | None = None,
    expected_language: str | None = None,
    expected_model: str = "whisper-1",
) -> None:
    """Assert basic transcription result validity.

    Args:
        result: TranscriptionResult to validate
        expected_text: Optional expected text content
        expected_language: Optional expected language code
        expected_model: Expected model name (default: whisper-1)
    """
    assert isinstance(result, TranscriptionResult)
    assert result.text is not None
    assert len(result.text) > 0
    assert result.language is not None
    assert result.model_name == expected_model
    assert result.audio_file is not None

    if expected_text is not None:
        assert result.text == expected_text

    if expected_language is not None:
        assert result.language == expected_language


def assert_transcription_result_segments(
    result: TranscriptionResult,
    min_segments: int = 0,
    expected_segment_text: str | None = None,
) -> None:
    """Assert segment-related expectations.

    Args:
        result: TranscriptionResult to validate
        min_segments: Minimum number of segments expected
        expected_segment_text: Optional text of first segment
    """
    assert result.segments is not None
    assert len(result.segments) >= min_segments

    if expected_segment_text is not None and len(result.segments) > 0:
        assert result.segments[0].text == expected_segment_text


def assert_transcription_result_usage(
    result: TranscriptionResult,
    should_exist: bool = True,
    expected_type: str | None = None,
) -> None:
    """Assert usage data expectations.

    Args:
        result: TranscriptionResult to validate
        should_exist: Whether usage data should exist
        expected_type: Expected usage type ("duration" or "tokens")
    """
    if should_exist:
        assert result.usage is not None
        if expected_type is not None:
            assert result.usage.type == expected_type
    else:
        assert result.usage is None


def make_audio_mock_chunk(idx: int, start: int, dur: int) -> AudioFileChunk:
    name = f"test_chunk_{idx}.mp3"
    data = b"fake audio data {idx}"
    return AudioFileChunk(
        filename=name,
        data=data,
        chunk_index=idx,
        total_chunks=1,
        start_time_ms=start,
        end_time_ms=start + dur,
        original_filename="test.mp3",
        original_path=Path("/fake/test.mp3"),
    )


def make_audio_transcription_segment() -> TranscriptionSegment:
    raise NotImplementedError()


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_success(mock_chunk_audio_file: Mock) -> None:
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

    mock_chunk_audio_file.return_value = [make_audio_mock_chunk(0, 0, 10500)]

    # Mock AsyncOpenAI client response
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
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Execute - use explicit client injection
    result = await transcribe_audio(audio_file, client=mock_client)

    # Verify using assertion helpers
    assert_transcription_result_ok(result, expected_text="Transcribed text", expected_language="en")
    assert_transcription_result_segments(
        result, min_segments=1, expected_segment_text="First segment"
    )
    assert_transcription_result_usage(result, should_exist=False)
    assert result.audio_file == audio_file.path
    assert result.duration == 10.5

    # Verify API was called with correct params
    mock_client.audio.transcriptions.create.assert_called_once()
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-1"
    assert call_kwargs["response_format"] == "verbose_json"


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_custom_options(mock_chunk: Mock) -> None:
    """Test transcription with custom options."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock chunk_audio_file
    mock_chunk_obj = AudioFileChunk(
        filename="test_chunk_0.mp3",
        data=audio_data,
        chunk_index=0,
        total_chunks=1,
        start_time_ms=0,
        end_time_ms=15000,
        original_filename="test.mp3",
        original_path=audio_file.path,
    )
    mock_chunk.return_value = [mock_chunk_obj]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Custom transcription"
    mock_response.language = "es"
    mock_response.duration = 15.0
    mock_response.segments = []
    mock_response.usage = None

    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Custom options
    options = TranscriptionOptions(
        model="gpt-4o-transcribe",
        language="es",
        temperature=0.3,
        prompt="Custom prompt",
    )

    result = await transcribe_audio(audio_file, options, client=mock_client)

    # Verify using assertion helpers
    assert_transcription_result_ok(
        result,
        expected_text="Custom transcription",
        expected_language="es",
        expected_model="gpt-4o-transcribe",
    )

    # Verify custom options were passed to API
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o-transcribe"
    assert call_kwargs["language"] == "es"
    assert call_kwargs["temperature"] == 0.3
    assert call_kwargs["prompt"] == "Custom prompt"
    assert call_kwargs["response_format"] == "verbose_json"  # Always forced


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_usage_data(mock_chunk: Mock) -> None:
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

    # Mock chunk_audio_file
    mock_chunk_obj = AudioFileChunk(
        filename="test_chunk_0.mp3",
        data=audio_data,
        chunk_index=0,
        total_chunks=1,
        start_time_ms=0,
        end_time_ms=120500,
        original_filename="test.mp3",
        original_path=audio_file.path,
    )
    mock_chunk.return_value = [mock_chunk_obj]

    mock_client = MagicMock()

    # Mock response with SDK UsageDuration
    usage = UsageDuration(type="duration", seconds=120.5)

    mock_response = MagicMock()
    mock_response.text = "Text"
    mock_response.language = "en"
    mock_response.duration = 120.5
    mock_response.segments = []
    mock_response.usage = usage

    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    result = await transcribe_audio(audio_file, client=mock_client)

    assert_transcription_result_usage(result, should_exist=True, expected_type="duration")
    assert result.usage is not None
    assert hasattr(result.usage, "seconds")
    assert result.usage.seconds == 120.5


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_token_usage(mock_chunk: Mock) -> None:
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

    # Mock chunk_audio_file
    mock_chunk_obj = AudioFileChunk(
        filename="test_chunk_0.mp3",
        data=audio_data,
        chunk_index=0,
        total_chunks=1,
        start_time_ms=0,
        end_time_ms=10000,
        original_filename="test.mp3",
        original_path=audio_file.path,
    )
    mock_chunk.return_value = [mock_chunk_obj]

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

    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    result = await transcribe_audio(audio_file, client=mock_client)

    assert_transcription_result_usage(result, should_exist=True, expected_type="tokens")
    assert result.usage is not None
    assert result.usage.type == "tokens"
    # After type check, mypy knows it's UsageTokens
    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 50
    assert result.usage.total_tokens == 150


@pytest.mark.asyncio
@patch("python.infra.whisper.dependencies.get_settings")
async def test_transcribe_audio_api_key_error(
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
        await transcribe_audio(audio_file)  # Will try to get client via DI

    assert "api_key" in str(exc_info.value).lower()


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_api_failure(mock_chunk: Mock) -> None:
    """Test that API failures are wrapped in TranscriptionError."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock chunk_audio_file
    mock_chunk_obj = AudioFileChunk(
        filename="test_chunk_0.mp3",
        data=audio_data,
        chunk_index=0,
        total_chunks=1,
        start_time_ms=0,
        end_time_ms=10000,
        original_filename="test.mp3",
        original_path=audio_file.path,
    )
    mock_chunk.return_value = [mock_chunk_obj]

    mock_client = MagicMock()

    # Simulate API error
    mock_client.audio.transcriptions.create = AsyncMock(side_effect=Exception("API error"))

    with pytest.raises(TranscriptionError) as exc_info:
        await transcribe_audio(audio_file, client=mock_client)

    assert "API transcription failed" in str(exc_info.value)
    assert "API error" in str(exc_info.value)
    assert exc_info.value.file_path == str(audio_file.path)


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_pydantic_validation(mock_chunk: Mock) -> None:
    """Test that Pydantic validates response data including segments."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock chunk_audio_file
    mock_chunk_obj = AudioFileChunk(
        filename="test_chunk_0.mp3",
        data=audio_data,
        chunk_index=0,
        total_chunks=1,
        start_time_ms=0,
        end_time_ms=5000,
        original_filename="test.mp3",
        original_path=audio_file.path,
    )
    mock_chunk.return_value = [mock_chunk_obj]

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

    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    result = await transcribe_audio(audio_file, client=mock_client)

    # Pydantic should have validated and converted segments to Segment models
    assert_transcription_result_segments(
        result, min_segments=1, expected_segment_text="Valid segment"
    )
    assert result.segments[0].id == 0
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 5.0


# Test new dependency override pattern


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_dependency_override(mock_chunk: Mock) -> None:
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

    # Mock chunk_audio_file
    mock_chunk_obj = AudioFileChunk(
        filename="test_chunk_0.mp3",
        data=audio_data,
        chunk_index=0,
        total_chunks=1,
        start_time_ms=0,
        end_time_ms=5000,
        original_filename="test.mp3",
        original_path=audio_file.path,
    )
    mock_chunk.return_value = [mock_chunk_obj]

    # Create mock client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Dependency override test"
    mock_response.language = "en"
    mock_response.duration = 5.0
    mock_response.segments = []
    mock_response.usage = None
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Use override_dependency context manager
    with override_dependency("client", lambda: mock_client):
        result = await transcribe_audio(audio_file)

    assert_transcription_result_ok(
        result, expected_text="Dependency override test", expected_language="en"
    )
    mock_client.audio.transcriptions.create.assert_called_once()


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_explicit_client_injection(mock_chunk: Mock) -> None:
    """Test explicitly passing client parameter (bypasses DI)."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock chunk_audio_file
    mock_chunk_obj = AudioFileChunk(
        filename="test_chunk_0.mp3",
        data=audio_data,
        chunk_index=0,
        total_chunks=1,
        start_time_ms=0,
        end_time_ms=8000,
        original_filename="test.mp3",
        original_path=audio_file.path,
    )
    mock_chunk.return_value = [mock_chunk_obj]

    # Create mock client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Explicit injection test"
    mock_response.language = "es"
    mock_response.duration = 8.0
    mock_response.segments = []
    mock_response.usage = None
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Explicitly pass client - no DI needed
    result = await transcribe_audio(audio_file, client=mock_client)

    assert_transcription_result_ok(
        result, expected_text="Explicit injection test", expected_language="es"
    )
    mock_client.audio.transcriptions.create.assert_called_once()
