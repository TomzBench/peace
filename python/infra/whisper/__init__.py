"""Whisper audio transcription module."""

from .audio import chunk_audio_file, open_audio_file_async
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
    AudioFileChunk,
    OpenAIFile,
    OpenAIRequestConfig,
    ResponseOptions,
    TranscriptionOptions,
    TranscriptionResult,
    TranslateOptions,
    UsageDuration,
    UsageTokens,
    flatten_options,
)

__all__ = [
    "AudioFile",
    "AudioFileChunk",
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
    "UsageDuration",
    "UsageTokens",
    "WhisperError",
    "chunk_audio_file",
    "clear_overrides",
    "flatten_options",
    "get_openai_client",
    "inject_deps",
    "open_audio_file_async",
    "override_dependency",
    "transcribe_audio",
]
