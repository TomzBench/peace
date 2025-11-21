"""Pydantic models for Whisper transcription data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Segment(BaseModel):
    """A transcribed segment with timing information."""

    id: int
    start: float  # Start time in seconds
    end: float  # End time in seconds
    text: str
    tokens: list[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float


class TranscriptionResult(BaseModel):
    """Complete transcription result from Whisper."""

    # Full transcription text
    text: str

    # Segmented transcription with timing
    segments: list[Segment] = Field(default_factory=list)

    # Detected language
    language: str

    # Metadata
    audio_file: Path
    model_name: str
    transcription_timestamp: datetime = Field(default_factory=datetime.now)
    duration: float | None = None  # Audio duration in seconds

    # Optional translation (if translate=True)
    translation: str | None = None


@dataclass
class TranscriptionBaseOptions:
    """Base options common to all Whisper transcription methods.

    These options are supported by both the OpenAI Whisper API and local models.
    """

    language: str | None = None  # Language code (e.g., "en", "es", "fr")
    temperature: float = 0.0  # Sampling temperature (0-1)
    initial_prompt: str | None = None  # Text to guide style/context


@dataclass
class TranscriptionApiOptions(TranscriptionBaseOptions):
    """Options for OpenAI Whisper API transcription.

    The API only supports the base options (language, temperature, initial_prompt).
    Uses the "whisper-1" model exclusively. For translation, use the separate
    transcribe_and_translate() function.
    """

    pass


@dataclass
class TranscriptionLocalOptions(TranscriptionBaseOptions):
    """Options for local Whisper model transcription.

    Provides full control over the Whisper model including advanced decoding
    parameters, model selection, and fine-tuning thresholds. These options
    are only available when running Whisper locally, not via the API.
    """

    # Model selection
    model: str = "base"  # Model size: tiny, base, small, medium, large
    task: str = "transcribe"  # Task: transcribe or translate

    # Advanced decoding parameters
    best_of: int | None = None  # Number of candidates when sampling
    beam_size: int | None = None  # Beam size for beam search
    patience: float | None = None  # Beam search patience factor
    length_penalty: float | None = None  # Length penalty for beam search

    # Token control
    suppress_tokens: str = "-1"  # Tokens to suppress (comma-separated)

    # Optimization settings
    condition_on_previous_text: bool = True  # Use previous text as context
    fp16: bool = True  # Use FP16 for faster inference

    # Quality thresholds
    compression_ratio_threshold: float | None = None  # Detect compression issues
    logprob_threshold: float | None = None  # Minimum average log probability
    no_speech_threshold: float | None = None  # Threshold for no-speech detection

    # Other options
    verbose: bool = False  # Enable verbose output
    whisper_kwargs: dict[str, Any] = field(default_factory=dict)  # Additional kwargs


# Backward compatibility alias - prefer TranscriptionApiOptions for new code
TranscriptionOptions = TranscriptionApiOptions
