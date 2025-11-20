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
    """Options for Whisper transcription."""

    model: str = "base"  # tiny, base, small, medium, large
    language: str | None = None  # Auto-detect if None
    task: str = "transcribe"  # "transcribe" or "translate"
    temperature: float = 0.0
    best_of: int | None = None
    beam_size: int | None = None
    patience: float | None = None
    length_penalty: float | None = None
    suppress_tokens: str = "-1"
    initial_prompt: str | None = None
    condition_on_previous_text: bool = True
    fp16: bool = True  # Use FP16 for faster inference
    compression_ratio_threshold: float | None = None
    logprob_threshold: float | None = None
    no_speech_threshold: float | None = None
    verbose: bool = False
    whisper_kwargs: dict[str, Any] = field(default_factory=dict)
