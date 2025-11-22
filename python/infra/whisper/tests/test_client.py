"""Tests for Whisper client."""

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from openai.types.audio.transcription import UsageDuration, UsageTokens

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


def make_mock_chunk(idx: int, start: int, dur: int) -> AudioFileChunk:
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


def make_mock_segment(n: int) -> TranscriptionSegment:
    text = f"test segment {n}"
    return TranscriptionSegment(
        id=n,
        seek=0,
        start=0.0,
        end=5.0,
        text=text,
        tokens=[1, 2, 3],
        temperature=0.0,
        avg_logprob=-0.2,
        compression_ratio=1.5,
        no_speech_prob=0.01,
    )


def make_mock_segments(count: int) -> list[TranscriptionSegment]:
    return [make_mock_segment(x) for x in range(count)]


@dataclass
class TranscriptionResultExpect:
    text: str
    duration: float
    segments: list[TranscriptionSegment] | None = None
    usage: UsageDuration | UsageTokens | None = None
    language: str = "en"

    def make_mock_response(self) -> type[MagicMock]:
        mock_response = MagicMock()
        mock_response.text = self.text
        mock_response.language = self.language
        mock_response.duration = self.duration
        mock_response.segments = self.segments
        mock_response.usage = self.usage
        return mock_response


def assert_transcription_result(result: TranscriptionResult, e: TranscriptionResultExpect) -> None:
    assert result.text == e.text
    assert result.language == e.language
    assert result.duration == e.duration
    assert result.usage == e.usage or (result.usage is None and e.usage is None)
    if e.segments is not None:
        assert result.segments is not None
        assert len(result.segments) == len(e.segments)
        assert all(x == y for x, y in zip(e.segments, result.segments, strict=False))
    pass


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
    expect = TranscriptionResultExpect(
        text="Transcribed text",
        duration=10.5,
        segments=make_mock_segments(1),
        language="en",
    )

    # Mock AsyncOpenAI client response
    mock_chunk_audio_file.return_value = [make_mock_chunk(0, 0, 10500)]
    mock_client = MagicMock()
    mock_response = expect.make_mock_response()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Execute - use explicit client injection
    result = await transcribe_audio(audio_file, client=mock_client)
    assert_transcription_result(result, expect)

    # Verify API was called with correct params
    mock_client.audio.transcriptions.create.assert_called_once()
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-1"
    assert call_kwargs["response_format"] == "verbose_json"


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_custom_options(mock_chunk_audio_file: Mock) -> None:
    """Test transcription with custom options."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create expectation with Spanish language
    expect = TranscriptionResultExpect(
        text="Custom transcription",
        duration=15.0,
        segments=[],
        language="es",
    )

    # Mock chunk and client
    mock_chunk_audio_file.return_value = [make_mock_chunk(0, 0, 15000)]
    mock_client = MagicMock()
    mock_response = expect.make_mock_response()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Custom options
    options = TranscriptionOptions(
        model="gpt-4o-transcribe",
        language="es",
        temperature=0.3,
        prompt="Custom prompt",
    )

    # Execute
    result = await transcribe_audio(audio_file, options, client=mock_client)

    # Assert using expect pattern
    assert_transcription_result(result, expect)
    assert result.model_name == "gpt-4o-transcribe"  # Custom model assertion

    # Verify custom options were passed to API
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o-transcribe"
    assert call_kwargs["language"] == "es"
    assert call_kwargs["temperature"] == 0.3
    assert call_kwargs["prompt"] == "Custom prompt"
    assert call_kwargs["response_format"] == "verbose_json"  # Always forced


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_usage_data(mock_chunk_audio_file: Mock) -> None:
    """Test transcription with SDK usage data (UsageDuration)."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create expectation with usage data
    expect = TranscriptionResultExpect(
        text="Text",
        duration=120.5,
        segments=[],
        usage=UsageDuration(type="duration", seconds=120.5),
        language="en",
    )

    # Mock chunk and client
    mock_chunk_audio_file.return_value = [make_mock_chunk(0, 0, 120500)]
    mock_client = MagicMock()
    mock_response = expect.make_mock_response()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Execute
    result = await transcribe_audio(audio_file, client=mock_client)

    # Assert using expect pattern (includes usage assertions)
    assert_transcription_result(result, expect)


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_token_usage(mock_chunk_audio_file: Mock) -> None:
    """Test transcription with SDK token-based usage data (UsageTokens)."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create expectation with token usage data
    expect = TranscriptionResultExpect(
        text="Text",
        duration=10.0,
        segments=[],
        usage=UsageTokens(
            type="tokens",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        ),
        language="en",
    )

    # Mock chunk and client
    mock_chunk_audio_file.return_value = [make_mock_chunk(0, 0, 10000)]
    mock_client = MagicMock()
    mock_response = expect.make_mock_response()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Execute
    result = await transcribe_audio(audio_file, client=mock_client)

    # Assert using expect pattern (includes usage assertions)
    assert_transcription_result(result, expect)


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


# Test new dependency override pattern


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_dependency_override(mock_chunk_audio_file: Mock) -> None:
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

    # Create expectation
    expect = TranscriptionResultExpect(
        text="Dependency override test",
        duration=5.0,
        segments=[],
        language="en",
    )

    # Mock chunk and client
    mock_chunk_audio_file.return_value = [make_mock_chunk(0, 0, 5000)]
    mock_client = MagicMock()
    mock_response = expect.make_mock_response()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Use override_dependency context manager
    with override_dependency("client", lambda: mock_client):
        result = await transcribe_audio(audio_file)

    # Assert using expect pattern
    assert_transcription_result(result, expect)
    mock_client.audio.transcriptions.create.assert_called_once()


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_with_explicit_client_injection(mock_chunk_audio_file: Mock) -> None:
    """Test explicitly passing client parameter (bypasses DI)."""
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create expectation with Spanish language
    expect = TranscriptionResultExpect(
        text="Explicit injection test",
        duration=8.0,
        segments=[],
        language="es",
    )

    # Mock chunk and client
    mock_chunk_audio_file.return_value = [make_mock_chunk(0, 0, 8000)]
    mock_client = MagicMock()
    mock_response = expect.make_mock_response()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Explicitly pass client - no DI needed
    result = await transcribe_audio(audio_file, client=mock_client)

    # Assert using expect pattern
    assert_transcription_result(result, expect)
    mock_client.audio.transcriptions.create.assert_called_once()
