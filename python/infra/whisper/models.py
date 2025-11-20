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
class TranscriptionOptions:
    """Options for Whisper transcription via OpenAI API.

    Note: This module now uses the OpenAI Whisper API. Many parameters from the
    local library are not supported. Supported parameters:
    - language: Language hint (ISO-639-1 code)
    - temperature: Sampling temperature (0-1)
    - initial_prompt: Text to guide transcription style

    Unsupported parameters (ignored by API):
    - model: Only "whisper-1" available (not tiny/base/small/medium/large)
    - task: Use transcribe_and_translate() for translation instead
    - best_of, beam_size, patience, length_penalty: Advanced decoding not exposed
    - condition_on_previous_text, fp16: Server-side optimizations
    - compression_ratio_threshold, logprob_threshold, no_speech_threshold: Auto-tuned
    - verbose, suppress_tokens: Not applicable to API
    """

    # Supported parameters
    language: str | None = None  # Language code (e.g., "en", "es", "fr")
    temperature: float = 0.0  # Sampling temperature (0-1)
    initial_prompt: str | None = None  # Text to guide style/context

    # Legacy parameters (unsupported by API, kept for backward compatibility)
    model: str = "base"  # Ignored: API only supports "whisper-1"
    task: str = "transcribe"  # Ignored: Use transcribe_and_translate() instead
    best_of: int | None = None  # Unsupported: Advanced decoding
    beam_size: int | None = None  # Unsupported: Advanced decoding
    patience: float | None = None  # Unsupported: Advanced decoding
    length_penalty: float | None = None  # Unsupported: Advanced decoding
    suppress_tokens: str = "-1"  # Unsupported
    condition_on_previous_text: bool = True  # Unsupported: Server-side
    fp16: bool = True  # Unsupported: Server-side optimization
    compression_ratio_threshold: float | None = None  # Unsupported: Auto-tuned
    logprob_threshold: float | None = None  # Unsupported: Auto-tuned
    no_speech_threshold: float | None = None  # Unsupported: Auto-tuned
    verbose: bool = False  # Unsupported
    whisper_kwargs: dict[str, Any] = field(default_factory=dict)  # Unsupported
