"""Whisper audio transcription module.

A functional wrapper around OpenAI Whisper for transcribing audio files
from YouTube videos or other sources.

Examples:
    Basic transcription:
    >>> from python.infra.whisper import transcribe_audio
    >>> from pathlib import Path
    >>> result = transcribe_audio(Path("audio.mp3"))
    >>> print(f"Language: {result.language}")
    >>> print(f"Text: {result.text}")

    Transcribe with specific model and language:
    >>> from python.infra.whisper import transcribe_audio, TranscriptionOptions
    >>> opts = TranscriptionOptions(model="small", language="en")
    >>> result = transcribe_audio(Path("audio.mp3"), opts)

    Transcribe and translate to English:
    >>> from python.infra.whisper import transcribe_and_translate
    >>> result = transcribe_and_translate(Path("spanish.mp3"))
    >>> print(f"English translation: {result.text}")

    Working with segments:
    >>> for segment in result.segments:
    ...     print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")

    Integration with YouTube module:
    >>> from python.infra.youtube import download_audio
    >>> from python.infra.whisper import transcribe_audio
    >>> video_info = download_audio("https://youtube.com/watch?v=...", Path("audio"))
    >>> result = transcribe_audio(video_info.downloaded_file)
"""

from python.infra.whisper.client import (
    load_model,
    transcribe_and_translate,
    transcribe_audio,
)
from python.infra.whisper.exceptions import (
    AudioFileError,
    ModelLoadError,
    TranscriptionError,
    WhisperError,
)
from python.infra.whisper.models import (
    Segment,
    TranscriptionOptions,
    TranscriptionResult,
)

__all__ = [
    "AudioFileError",
    "ModelLoadError",
    "Segment",
    "TranscriptionError",
    "TranscriptionOptions",
    "TranscriptionResult",
    "WhisperError",
    "load_model",
    "transcribe_and_translate",
    "transcribe_audio",
]
