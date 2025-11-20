"""Tests for Whisper client functions."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from python.infra.whisper.client import (
    _parse_segments,
    _validate_audio_file,
    load_model,
    transcribe_and_translate,
    transcribe_audio,
)
from python.infra.whisper.exceptions import (
    AudioFileError,
    ModelLoadError,
    TranscriptionError,
)
from python.infra.whisper.models import TranscriptionOptions


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


@patch("python.infra.whisper.client.whisper")
def test_load_model(mock_whisper: MagicMock) -> None:
    """Test loading a Whisper model."""
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model

    # Clear cache before test
    from python.infra.whisper.client import _model_cache

    _model_cache.clear()

    model = load_model("base")

    assert model == mock_model
    mock_whisper.load_model.assert_called_once_with("base")


@patch("python.infra.whisper.client.whisper")
def test_load_model_caching(mock_whisper: MagicMock) -> None:
    """Test that models are cached after first load."""
    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model

    # Clear cache before test
    from python.infra.whisper.client import _model_cache

    _model_cache.clear()

    # First load
    model1 = load_model("small")
    # Second load (should use cache)
    model2 = load_model("small")

    assert model1 == model2
    # Should only call load_model once due to caching
    mock_whisper.load_model.assert_called_once_with("small")


@patch("python.infra.whisper.client.whisper")
def test_load_model_failure(mock_whisper: MagicMock) -> None:
    """Test model loading failure."""
    mock_whisper.load_model.side_effect = Exception("Model not found")

    with pytest.raises(ModelLoadError) as exc_info:
        load_model("invalid-model")

    assert "invalid-model" in str(exc_info.value)
    assert exc_info.value.model_name == "invalid-model"


@patch("python.infra.whisper.client.whisper")
def test_transcribe_audio(
    mock_whisper: MagicMock,
    temp_audio_file: Path,
    mock_whisper_result: dict[str, Any],
) -> None:
    """Test transcribing an audio file."""
    # Setup mock
    mock_model = MagicMock()
    mock_model.transcribe.return_value = mock_whisper_result
    mock_whisper.load_model.return_value = mock_model

    # Clear cache
    from python.infra.whisper.client import _model_cache

    _model_cache.clear()

    # Transcribe
    result = transcribe_audio(temp_audio_file)

    # Verify result
    assert result.text == "Hello, this is a test transcription."
    assert len(result.segments) == 2
    assert result.language == "en"
    assert result.audio_file == temp_audio_file
    assert result.model_name == "base"
    assert result.duration == 4.0

    # Verify model.transcribe was called correctly
    mock_model.transcribe.assert_called_once()
    call_args = mock_model.transcribe.call_args
    assert str(temp_audio_file) in call_args[0]


@patch("python.infra.whisper.client.whisper")
def test_transcribe_audio_with_options(
    mock_whisper: MagicMock,
    temp_audio_file: Path,
    mock_whisper_result: dict[str, Any],
) -> None:
    """Test transcribing with custom options."""
    # Setup mock
    mock_model = MagicMock()
    mock_model.transcribe.return_value = mock_whisper_result
    mock_whisper.load_model.return_value = mock_model

    # Clear cache
    from python.infra.whisper.client import _model_cache

    _model_cache.clear()

    # Transcribe with options
    options = TranscriptionOptions(
        model="small",
        language="en",
        temperature=0.5,
        initial_prompt="This is a test",
    )
    result = transcribe_audio(temp_audio_file, options)

    # Verify result
    assert result.model_name == "small"

    # Verify transcribe was called with correct parameters
    call_kwargs = mock_model.transcribe.call_args[1]
    assert call_kwargs["language"] == "en"
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["initial_prompt"] == "This is a test"


@patch("python.infra.whisper.client.whisper")
def test_transcribe_audio_file_not_found(
    mock_whisper: MagicMock,
    invalid_audio_file: Path,
) -> None:
    """Test transcribing a missing audio file."""
    with pytest.raises(AudioFileError):
        transcribe_audio(invalid_audio_file)


@patch("python.infra.whisper.client.whisper")
def test_transcribe_audio_model_load_error(
    mock_whisper: MagicMock,
    temp_audio_file: Path,
) -> None:
    """Test transcription when model fails to load."""
    mock_whisper.load_model.side_effect = Exception("Model load failed")

    with pytest.raises(ModelLoadError):
        transcribe_audio(temp_audio_file)


@patch("python.infra.whisper.client.whisper")
def test_transcribe_audio_transcription_error(
    mock_whisper: MagicMock,
    temp_audio_file: Path,
) -> None:
    """Test transcription failure."""
    # Setup mock
    mock_model = MagicMock()
    mock_model.transcribe.side_effect = Exception("Transcription failed")
    mock_whisper.load_model.return_value = mock_model

    # Clear cache
    from python.infra.whisper.client import _model_cache

    _model_cache.clear()

    with pytest.raises(TranscriptionError) as exc_info:
        transcribe_audio(temp_audio_file)

    assert "Transcription failed" in str(exc_info.value)


@patch("python.infra.whisper.client.whisper")
def test_transcribe_and_translate(
    mock_whisper: MagicMock,
    temp_audio_file: Path,
    mock_translated_result: dict[str, Any],
) -> None:
    """Test transcribing and translating to English."""
    # Setup mock
    mock_model = MagicMock()
    mock_model.transcribe.return_value = mock_translated_result
    mock_whisper.load_model.return_value = mock_model

    # Clear cache
    from python.infra.whisper.client import _model_cache

    _model_cache.clear()

    # Transcribe and translate
    result = transcribe_and_translate(temp_audio_file)

    # Verify result
    assert result.text == "Hello, this is an English translation."
    assert result.translation == "Hello, this is an English translation."
    assert result.language == "es"  # Original language

    # Verify task was set to "translate"
    call_kwargs = mock_model.transcribe.call_args[1]
    assert call_kwargs["task"] == "translate"


@patch("python.infra.whisper.client.whisper")
def test_transcribe_and_translate_with_options(
    mock_whisper: MagicMock,
    temp_audio_file: Path,
    mock_translated_result: dict[str, Any],
) -> None:
    """Test transcribe_and_translate overrides task option."""
    # Setup mock
    mock_model = MagicMock()
    mock_model.transcribe.return_value = mock_translated_result
    mock_whisper.load_model.return_value = mock_model

    # Clear cache
    from python.infra.whisper.client import _model_cache

    _model_cache.clear()

    # Try to set task to "transcribe", should be overridden to "translate"
    options = TranscriptionOptions(task="transcribe", model="small")
    result = transcribe_and_translate(temp_audio_file, options)

    # Verify task was overridden
    call_kwargs = mock_model.transcribe.call_args[1]
    assert call_kwargs["task"] == "translate"
    assert result.translation is not None  # Ensure translation field is set
