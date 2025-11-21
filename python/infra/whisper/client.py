"""Functional wrapper for OpenAI Whisper API transcription."""

import logging
from dataclasses import asdict
from datetime import datetime

from openai import OpenAI

from .dependencies import inject_deps
from .exceptions import TranscriptionError
from .models import (
    AudioFile,
    ResponseOptions,
    TranscriptionOptions,
    TranscriptionResult,
    flatten_options,
)

logger = logging.getLogger(__name__)


@inject_deps
def transcribe_audio(
    audio_file: AudioFile,
    options: TranscriptionOptions | None = None,
    client: OpenAI | None = None,
) -> TranscriptionResult:
    """Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_file: AudioFile with validated audio data and metadata
        options: Transcription options with composable request/response config
        client: OpenAI client (auto-injected if None via @inject_deps)

    Returns:
        TranscriptionResult with text, segments, metadata, and usage info

    Raises:
        TranscriptionError: If transcription fails (wraps OpenAI SDK errors)
    """
    options = options or TranscriptionOptions()
    logger.info(f"Transcribing audio file via OpenAI API: {audio_file.filename}")

    # Ensure client is injected (decorator should handle this)
    assert client is not None, "OpenAI client must be provided or injected"

    # Perform transcription
    try:
        # Pass file tuple directly to SDK via .file property
        response = client.audio.transcriptions.create(
            file=audio_file.file, **flatten_options(options), **asdict(ResponseOptions())
        )

        # Build transcription result - using SDK types directly (no conversion needed)
        transcription_result = TranscriptionResult(
            object="transcription",
            usage=response.usage if hasattr(response, "usage") else None,
            text=response.text,
            segments=response.segments or [],
            language=response.language,
            duration=response.duration,
            audio_file=audio_file.path,
            model_name=options.model,
            transcription_timestamp=datetime.now(),
        )

        logger.info(f"Successfully transcribed: {transcription_result!r}")

        return transcription_result

    except Exception as e:
        # Wrap all errors in TranscriptionError with context
        raise TranscriptionError(
            f"API transcription failed for {audio_file.filename}: {e}",
            str(audio_file.path),
        ) from e
