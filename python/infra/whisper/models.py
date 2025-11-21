"""Pydantic models for Whisper transcription data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from openai.types.audio import TranscriptionSegment
from openai.types.audio.transcription import Usage
from pydantic import BaseModel, Field

# Re-export SDK types for convenience
Segment = TranscriptionSegment


class OpenAIFile(BaseModel):
    """Base class for files that can be sent to OpenAI APIs.

    Provides universal OpenAI SDK compatibility through the .file property
    which returns the (filename, bytes) tuple format accepted by all
    OpenAI file upload endpoints.
    """

    filename: str  # Filename with extension
    data: bytes  # File contents as bytes

    @property
    def file(self) -> tuple[str, bytes]:
        """Get OpenAI SDK-compatible tuple format.

        Returns:
            Tuple of (filename, data) ready for any OpenAI file upload API

        Examples:
            >>> openai_file = OpenAIFile(filename="audio.mp3", data=b"...")
            >>> client.audio.transcriptions.create(file=openai_file.file)
        """
        return (self.filename, self.data)


class AudioFile(OpenAIFile):
    """Audio file with metadata.

    Inherits from OpenAIFile and adds audio-specific metadata.
    Can be passed to OpenAI audio APIs via the .file property.
    """

    path: Path  # Full path to audio file
    size: int  # File size in bytes
    extension: str  # File extension (e.g., ".mp3")

# Composable base classes (OpenAI API patterns)
# Defined first so they can be referenced by result/option classes


@dataclass
class OpenAIRequestConfig:
    """Low-level request configuration for OpenAI API calls.

    These options apply to the HTTP request itself, not the API logic.
    Common across all OpenAI endpoints.
    """

    extra_headers: dict[str, str] | None = None  # Additional HTTP headers
    extra_query: dict[str, str] | None = None  # Additional query parameters
    extra_body: dict[str, Any] | None = None  # Additional body fields
    timeout: float | None = None  # Request timeout in seconds


@dataclass
class ResponseOptions:
    """Response formatting options common across OpenAI APIs.

    Note: Not audio-specific - used by chat, embeddings, etc.
    """

    response_format: str = "verbose_json"  # json, text, srt, verbose_json, vtt, etc.
    stream: bool = False  # Enable Server-Sent Events streaming


# Pydantic models for API responses


class TranscriptionResult(BaseModel):
    """Complete transcription result from Whisper.

    Includes both OpenAI API response metadata and our wrapper metadata.
    Uses OpenAI SDK types directly for segments and usage.
    """

    # OpenAI API response fields (using SDK types)
    object: str = "transcription"  # Resource type from API
    usage: Usage | None = None  # SDK Union[UsageDuration, UsageTokens]

    # Transcription data (using SDK types)
    text: str  # Full transcription text
    segments: list[TranscriptionSegment] = Field(default_factory=list)  # SDK type
    language: str  # Detected or specified language
    duration: float | None = None  # Audio duration in seconds

    # Wrapper metadata
    audio_file: Path  # Source audio file path
    model_name: str  # Model used (whisper-1, gpt-4o-transcribe, etc.)
    transcription_timestamp: datetime = Field(default_factory=datetime.now)

    # Optional fields
    translation: str | None = None  # English translation (if applicable)

    def __repr__(self) -> str:
        """Compact string representation suitable for logging."""
        duration_str = f"{self.duration:.1f}s" if self.duration else "unknown"
        return (
            f"TranscriptionResult("
            f"file={self.audio_file.name!r}, "
            f"chars={len(self.text)}, "
            f"segments={len(self.segments)}, "
            f"language={self.language!r}, "
            f"duration={duration_str}, "
            f"model={self.model_name!r}"
            f")"
        )


# Request options (dataclasses with composition)


# client.audio.transcriptions.create(...) args
@dataclass
class TranscriptionOptions:
    """Options for OpenAI Whisper API transcriptions.create() endpoint.

    Uses composition pattern to include common OpenAI request/response options.
    Endpoint-specific parameters are defined directly on this class.
    """

    # Model selection
    model: str = "whisper-1"  # whisper-1, gpt-4o-transcribe, gpt-4o-mini-transcribe

    # Transcription-specific parameters
    language: str | None = None  # ISO-639-1 language code (e.g., "en", "es", "fr")
    prompt: str | None = None  # Text to guide transcription style/context
    temperature: float = 0.0  # Sampling temperature (0-1)
    timestamp_granularities: list[str] | None = None  # ["word", "segment"]

    request_config: OpenAIRequestConfig = field(default_factory=OpenAIRequestConfig)


# client.audio.translations.create(...) args
@dataclass
class TranslateOptions:
    """Options for OpenAI Whisper API translations.create() endpoint.

    Uses composition pattern to include common OpenAI request/response options.
    Note: No language parameter - API auto-detects source and translates to English.
    """

    # Model selection
    model: str = "whisper-1"  # Currently only whisper-1 supports translation

    # Translation-specific parameters
    prompt: str | None = None  # Text to guide translation (should be in English)
    temperature: float = 0.0  # Sampling temperature (0-1)

    # Composed options (OpenAI patterns)
    request_config: OpenAIRequestConfig = field(default_factory=OpenAIRequestConfig)


# Utility functions for composable models


def flatten_options(
    opts: Any,
    exclude_fields: set[str] | None = None,
    exclude_none: bool = True,
) -> dict[str, Any]:
    """Flatten a composable dataclass into a flat dict for API calls.

    Recursively merges fields from nested dataclasses into a single flat dict.
    Useful for converting composable option objects into the flat parameter
    structure expected by API clients.

    Args:
        opts: Dataclass instance with potentially nested dataclass fields
        exclude_fields: Field names to exclude from flattening (e.g., 'request_config')
        exclude_none: Filter out None values from result

    Returns:
        Flattened dict suitable for API calls
    """
    from dataclasses import asdict

    exclude_fields = exclude_fields or set()
    result = {}

    # Convert dataclass to dict (recursively converts nested dataclasses)
    fields_dict = asdict(opts)

    for field_name, field_value in fields_dict.items():
        # Skip excluded fields
        if field_name in exclude_fields:
            continue

        # Nested dataclass becomes nested dict via asdict()
        # Flatten by merging nested fields directly into result
        if isinstance(field_value, dict) and field_value:
            result.update(field_value)
        else:
            result[field_name] = field_value

    # Filter out None values if requested
    if exclude_none:
        result = {k: v for k, v in result.items() if v is not None}

    return result
