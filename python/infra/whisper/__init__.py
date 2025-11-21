"""Whisper audio transcription module.

A functional wrapper around the OpenAI Whisper API for transcribing audio files
from YouTube videos or other sources.

Note: This module uses the OpenAI Whisper API (not the local library). You need to
configure your OpenAI API key via the OPENAI_API_KEY environment variable or in
config.yaml. API usage costs $0.006 per minute of audio.

Examples:
    Basic transcription:
    >>> from python.infra.whisper import transcribe_audio
    >>> from pathlib import Path
    >>> result = transcribe_audio(Path("audio.mp3"))
    >>> print(f"Language: {result.language}")
    >>> print(f"Text: {result.text}")

    Transcribe with language and temperature:
    >>> from python.infra.whisper import transcribe_audio, TranscriptionOptions
    >>> opts = TranscriptionOptions(language="en", temperature=0.2)
    >>> result = transcribe_audio(Path("audio.mp3"), opts)

    Working with segments:
    >>> for segment in result.segments:
    ...     print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")

    Integration with YouTube module:
    >>> from python.infra.youtube import download_audio
    >>> from python.infra.whisper import transcribe_audio
    >>> video_info = download_audio("https://youtube.com/watch?v=...", Path("audio"))
    >>> result = transcribe_audio(video_info.downloaded_file)
"""

from python.infra.whisper.client import transcribe_audio
from python.infra.whisper.exceptions import (
    AudioFileError,
    ModelLoadError,
    TranscriptionError,
    WhisperError,
)
from python.infra.whisper.models import (
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
    "AudioFileError",
    "ModelLoadError",
    "OpenAIRequestConfig",
    "ResponseOptions",
    "Segment",
    "TranscriptionError",
    "TranscriptionOptions",
    "TranscriptionResult",
    "TranslateOptions",
    "Usage",
    "WhisperError",
    "flatten_options",
    "transcribe_audio",
]
