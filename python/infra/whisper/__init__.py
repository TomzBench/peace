"""Whisper audio transcription module."""

from .client import transcribe_audio
from .dependencies import (
    clear_overrides,
    get_openai_client,
    inject_deps,
    override_dependency,
)
from .exceptions import (
    AudioFileError,
    ModelLoadError,
    TranscriptionError,
    WhisperError,
)
from .models import (
    AudioFile,
    OpenAIFile,
    OpenAIRequestConfig,
    ResponseOptions,
    Segment,
    TranscriptionOptions,
    TranscriptionResult,
    TranslateOptions,
    Usage,  # Re-exported SDK type
    flatten_options,
)

__all__ = [
    "AudioFile",
    "AudioFileError",
    "ModelLoadError",
    "OpenAIFile",
    "OpenAIRequestConfig",
    "ResponseOptions",
    "Segment",
    "TranscriptionError",
    "TranscriptionOptions",
    "TranscriptionResult",
    "TranslateOptions",
    "Usage",
    "WhisperError",
    "clear_overrides",
    "flatten_options",
    "get_openai_client",
    "inject_deps",
    "override_dependency",
    "transcribe_audio",
]
