"""Tests for Whisper models."""

from datetime import datetime
from pathlib import Path

from python.infra.whisper.models import (
    Segment,
    TranscriptionOptions,
    TranscriptionResult,
)


def test_segment_creation() -> None:
    """Test creating a Segment model."""
    segment = Segment(
        id=0,
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
    """Test TranscriptionResult with segments."""
    segments = [
        Segment(
            id=0,
            start=0.0,
            end=2.0,
            text="First segment",
            tokens=[1, 2],
            temperature=0.0,
            avg_logprob=-0.2,
            compression_ratio=1.5,
            no_speech_prob=0.01,
        ),
        Segment(
            id=1,
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


def test_transcription_options_defaults() -> None:
    """Test TranscriptionOptions default values."""
    options = TranscriptionOptions()

    assert options.model == "base"
    assert options.language is None
    assert options.task == "transcribe"
    assert options.temperature == 0.0
    assert options.best_of is None
    assert options.beam_size is None
    assert options.patience is None
    assert options.length_penalty is None
    assert options.suppress_tokens == "-1"
    assert options.initial_prompt is None
    assert options.condition_on_previous_text is True
    assert options.fp16 is True
    assert options.compression_ratio_threshold is None
    assert options.logprob_threshold is None
    assert options.no_speech_threshold is None
    assert options.verbose is False
    assert options.whisper_kwargs == {}


def test_transcription_options_custom() -> None:
    """Test TranscriptionOptions with custom values."""
    options = TranscriptionOptions(
        model="small",
        language="en",
        task="translate",
        temperature=0.5,
        fp16=False,
        verbose=True,
    )

    assert options.model == "small"
    assert options.language == "en"
    assert options.task == "translate"
    assert options.temperature == 0.5
    assert options.fp16 is False
    assert options.verbose is True


def test_transcription_options_with_kwargs() -> None:
    """Test TranscriptionOptions with additional kwargs."""
    options = TranscriptionOptions(
        whisper_kwargs={"custom_param": "value", "another_param": 42}
    )

    assert options.whisper_kwargs == {"custom_param": "value", "another_param": 42}
