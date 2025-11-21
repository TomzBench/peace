"""Tests for Whisper models."""

from datetime import datetime
from pathlib import Path

from python.infra.whisper.models import (
    OpenAIRequestConfig,
    ResponseOptions,
    TranscriptionOptions,
    TranscriptionResult,
    TranscriptionSegment,
    TranslateOptions,
    flatten_options,
)


def test_segment_creation() -> None:
    """Test creating a TranscriptionSegment model (SDK TranscriptionSegment)."""
    segment = TranscriptionSegment(
        id=0,
        seek=0,  # SDK field
        start=0.0,
        end=2.5,
        text="Hello world",
        tokens=[1, 2, 3],
        temperature=0.0,
        avg_logprob=-0.25,
        compression_ratio=1.5,
        no_speech_prob=0.01,
    )

    assert segment.id == 0
    assert segment.seek == 0
    assert segment.start == 0.0
    assert segment.end == 2.5
    assert segment.text == "Hello world"
    assert segment.tokens == [1, 2, 3]
    assert segment.temperature == 0.0
    assert segment.avg_logprob == -0.25
    assert segment.compression_ratio == 1.5
    assert segment.no_speech_prob == 0.01


def test_transcription_result_creation() -> None:
    """Test creating a TranscriptionResult model."""
    audio_file = Path("/tmp/test.mp3")
    timestamp = datetime.now()

    result = TranscriptionResult(
        text="Full transcription text",
        segments=[],
        language="en",
        audio_file=audio_file,
        model_name="base",
        transcription_timestamp=timestamp,
        duration=10.5,
    )

    assert result.text == "Full transcription text"
    assert result.segments == []
    assert result.language == "en"
    assert result.audio_file == audio_file
    assert result.model_name == "base"
    assert result.transcription_timestamp == timestamp
    assert result.duration == 10.5
    assert result.translation is None


def test_transcription_result_with_segments() -> None:
    """Test TranscriptionResult with segments (SDK TranscriptionSegment)."""
    segments = [
        TranscriptionSegment(
            id=0,
            seek=0,
            start=0.0,
            end=2.0,
            text="First segment",
            tokens=[1, 2],
            temperature=0.0,
            avg_logprob=-0.2,
            compression_ratio=1.5,
            no_speech_prob=0.01,
        ),
        TranscriptionSegment(
            id=1,
            seek=100,
            start=2.0,
            end=4.0,
            text="Second segment",
            tokens=[3, 4],
            temperature=0.0,
            avg_logprob=-0.3,
            compression_ratio=1.6,
            no_speech_prob=0.02,
        ),
    ]

    result = TranscriptionResult(
        text="First segment Second segment",
        segments=segments,
        language="en",
        audio_file=Path("/tmp/test.mp3"),
        model_name="base",
    )

    assert len(result.segments) == 2
    assert result.segments[0].text == "First segment"
    assert result.segments[1].text == "Second segment"


def test_transcription_result_with_translation() -> None:
    """Test TranscriptionResult with translation."""
    result = TranscriptionResult(
        text="Original text",
        language="es",
        audio_file=Path("/tmp/test.mp3"),
        model_name="base",
        translation="Translated text",
    )

    assert result.text == "Original text"
    assert result.translation == "Translated text"


def test_openai_request_config_defaults() -> None:
    """Test OpenAIRequestConfig default values."""
    config = OpenAIRequestConfig()

    assert config.extra_headers is None
    assert config.extra_query is None
    assert config.extra_body is None
    assert config.timeout is None


def test_openai_request_config_custom() -> None:
    """Test OpenAIRequestConfig with custom values."""
    config = OpenAIRequestConfig(
        extra_headers={"X-Custom": "value"},
        extra_query={"param": "test"},
        timeout=30.0,
    )

    assert config.extra_headers == {"X-Custom": "value"}
    assert config.extra_query == {"param": "test"}
    assert config.timeout == 30.0


def test_response_options_defaults() -> None:
    """Test ResponseOptions default values."""
    options = ResponseOptions()

    assert options.response_format == "verbose_json"
    assert options.stream is False


def test_usage_duration_type() -> None:
    """Test SDK Usage with duration-based billing (UsageDuration)."""
    from openai.types.audio.transcription import UsageDuration

    usage = UsageDuration(type="duration", seconds=120.5)

    assert usage.type == "duration"
    assert usage.seconds == 120.5


def test_usage_tokens_type() -> None:
    """Test SDK Usage with token-based billing (UsageTokens)."""
    from openai.types.audio.transcription import UsageTokens

    usage = UsageTokens(
        type="tokens",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
    )

    assert usage.type == "tokens"
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.total_tokens == 150


def test_transcription_options_defaults() -> None:
    """Test TranscriptionOptions default values."""
    options = TranscriptionOptions()

    assert options.model == "whisper-1"
    assert options.language is None
    assert options.prompt is None
    assert options.temperature == 0.0
    assert options.timestamp_granularities is None
    assert isinstance(options.request_config, OpenAIRequestConfig)


def test_transcription_options_custom() -> None:
    """Test TranscriptionOptions with custom values."""
    options = TranscriptionOptions(
        model="gpt-4o-transcribe",
        language="en",
        prompt="Transcription test",
        temperature=0.2,
        timestamp_granularities=["word", "segment"],
        request_config=OpenAIRequestConfig(timeout=60.0),
    )

    assert options.model == "gpt-4o-transcribe"
    assert options.language == "en"
    assert options.prompt == "Transcription test"
    assert options.temperature == 0.2
    assert options.timestamp_granularities == ["word", "segment"]
    assert options.request_config.timeout == 60.0


def test_translate_options_defaults() -> None:
    """Test TranslateOptions default values."""
    options = TranslateOptions()

    assert options.model == "whisper-1"
    assert options.prompt is None
    assert options.temperature == 0.0
    assert isinstance(options.request_config, OpenAIRequestConfig)


def test_translate_options_custom() -> None:
    """Test TranslateOptions with custom values."""
    options = TranslateOptions(
        model="whisper-1",
        prompt="Translation prompt",
        temperature=0.3,
    )

    assert options.model == "whisper-1"
    assert options.prompt == "Translation prompt"
    assert options.temperature == 0.3


def test_flatten_options_basic() -> None:
    """Test flatten_options with basic TranscriptionOptions."""
    options = TranscriptionOptions(
        model="whisper-1",
        language="en",
        temperature=0.2,
    )

    result = flatten_options(options)

    assert result["model"] == "whisper-1"
    assert result["language"] == "en"
    assert result["temperature"] == 0.2
    assert "response" not in result  # Nested object flattened
    assert "request_config" not in result  # Nested object flattened


def test_flatten_options_with_nested() -> None:
    """Test flatten_options with custom nested options."""
    options = TranscriptionOptions(
        model="gpt-4o-transcribe",
        request_config=OpenAIRequestConfig(timeout=30.0, extra_headers={"X-Test": "value"}),
    )

    result = flatten_options(options)

    assert result["model"] == "gpt-4o-transcribe"
    assert result["timeout"] == 30.0
    assert result["extra_headers"] == {"X-Test": "value"}


def test_flatten_options_exclude_none() -> None:
    """Test flatten_options filters None values by default."""
    options = TranscriptionOptions(
        model="whisper-1",
        language=None,  # Should be excluded
        prompt=None,  # Should be excluded
    )

    result = flatten_options(options, exclude_none=True)

    assert "language" not in result
    assert "prompt" not in result
    assert result["model"] == "whisper-1"


def test_flatten_options_exclude_fields() -> None:
    """Test flatten_options with exclude_fields parameter."""
    options = TranscriptionOptions(
        model="whisper-1",
        language="en",
        temperature=0.2,
    )

    result = flatten_options(options, exclude_fields={"temperature"})

    assert result["model"] == "whisper-1"
    assert result["language"] == "en"
    assert "temperature" not in result  # Excluded
