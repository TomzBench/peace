"""Pytest configuration and shared fixtures for Whisper tests."""

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def mock_whisper_result() -> dict[str, Any]:
    """Fixture providing mock Whisper transcription result.

    Returns:
        Mock result dict from Whisper transcribe()
    """
    return {
        "text": "Hello, this is a test transcription.",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "Hello, this is a test",
                "tokens": [1, 2, 3, 4, 5],
                "temperature": 0.0,
                "avg_logprob": -0.25,
                "compression_ratio": 1.5,
                "no_speech_prob": 0.01,
            },
            {
                "id": 1,
                "start": 2.5,
                "end": 4.0,
                "text": " transcription.",
                "tokens": [6, 7, 8],
                "temperature": 0.0,
                "avg_logprob": -0.30,
                "compression_ratio": 1.6,
                "no_speech_prob": 0.02,
            },
        ],
        "language": "en",
        "duration": 4.0,
    }


@pytest.fixture
def mock_translated_result() -> dict[str, Any]:
    """Fixture providing mock Whisper translation result.

    Returns:
        Mock result dict from Whisper transcribe() with translation
    """
    return {
        "text": "Hello, this is an English translation.",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 4.0,
                "text": "Hello, this is an English translation.",
                "tokens": [1, 2, 3, 4, 5, 6, 7, 8],
                "temperature": 0.0,
                "avg_logprob": -0.28,
                "compression_ratio": 1.55,
                "no_speech_prob": 0.015,
            }
        ],
        "language": "es",  # Original language was Spanish
        "duration": 4.0,
    }


@pytest.fixture
def temp_audio_file(tmp_path: Path) -> Path:
    """Fixture providing a temporary audio file path.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary audio file
    """
    audio_file = tmp_path / "test_audio.mp3"
    # Create an empty file (actual audio content not needed for most tests)
    audio_file.write_bytes(b"fake audio content")
    return audio_file


@pytest.fixture
def invalid_audio_file(tmp_path: Path) -> Path:
    """Fixture providing an invalid audio file path.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to file that doesn't exist
    """
    return tmp_path / "nonexistent.mp3"
