"""Functional wrapper for OpenAI Whisper API transcription."""

import logging
from datetime import datetime
from pathlib import Path
from textwrap import dedent

from openai import OpenAI

from python.config.settings import get_settings
from python.infra.whisper.exceptions import (
    AudioFileError,
    TranscriptionError,
    WhisperError,
)
from python.infra.whisper.models import (
    TranscriptionOptions,
    TranscriptionResult,
    flatten_options,
)

logger = logging.getLogger(__name__)

# File size limit for OpenAI API (25MB)
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _get_client() -> OpenAI:
    """Get configured OpenAI client.

    Returns:
        Configured OpenAI client instance

    Raises:
        WhisperError: If API key is not configured
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise WhisperError(
            "OpenAI API key not configured. Set OPENAI_API_KEY environment variable "
            "or configure openai_api_key in config.yaml"
        )

    logger.debug("Initializing OpenAI client")
    return OpenAI(
        api_key=settings.openai_api_key,
        organization=settings.openai_organization,
    )


def _validate_audio_file(audio_path: Path) -> None:
    """Validate that audio file exists, is readable, and meets API requirements.

    Args:
        audio_path: Path to audio file

    Raises:
        AudioFileError: If file is invalid, missing, or exceeds size limit
    """
    if not audio_path.exists():
        raise AudioFileError(f"Audio file not found: {audio_path}", str(audio_path))

    if not audio_path.is_file():
        raise AudioFileError(f"Path is not a file: {audio_path}", str(audio_path))

    # Check file size (OpenAI API limit: 25MB)
    file_size = audio_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise AudioFileError(
            f"File size {file_size / 1024 / 1024:.1f}MB exceeds "
            f"OpenAI API limit of {MAX_FILE_SIZE_MB}MB",
            str(audio_path),
        )

    # Check file extension
    valid_extensions = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".webm", ".mp4"}
    if audio_path.suffix.lower() not in valid_extensions:
        logger.warning(
            f"Audio file has unusual extension: {audio_path.suffix}. "
            f"Supported formats: {', '.join(sorted(valid_extensions))}"
        )




def transcribe_audio(
    audio_path: Path,
    options: TranscriptionOptions | None = None,
) -> TranscriptionResult:
    """Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_path: Path to audio file (mp3, wav, m4a, etc.) - max 25MB
        options: Transcription options with composable request/response config

    Returns:
        TranscriptionResult with text, segments, metadata, and usage info

    Raises:
        AudioFileError: If audio file is invalid, missing, or exceeds 25MB
        WhisperError: If API key is not configured
        TranscriptionError: If transcription fails

    Examples:
        >>> from pathlib import Path
        >>> result = transcribe_audio(Path("audio.mp3"))
        >>> print(f"Language: {result.language}, Text: {result.text}")

        >>> from python.infra.whisper.models import TranscriptionOptions, ResponseOptions
        >>> opts = TranscriptionOptions(
        ...     model="gpt-4o-transcribe",
        ...     language="en",
        ...     temperature=0.2,
        ...     response=ResponseOptions(response_format="json")
        ... )
        >>> result = transcribe_audio(Path("audio.mp3"), opts)
    """
    options = options or TranscriptionOptions()
    logger.info(f"Transcribing audio file via OpenAI API: {audio_path}")

    # Flatten all composable options into API parameters
    api_params = flatten_options(options)

    # Force verbose_json format to get rich response (segments, language, duration)
    # This simplifies our API - we always return complete data regardless of caller's intent
    api_params["response_format"] = "verbose_json"

    # Perform transcription
    try:
        # Get OpenAI client
        client = _get_client()

        # Validate audio file
        _validate_audio_file(audio_path)

        # read audio and transcribe
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                file=audio_file,
                **api_params,
            )

        # Build transcription result - using SDK types directly (no conversion needed)
        transcription_result = TranscriptionResult(
            object="transcription",
            usage=response.usage if hasattr(response, "usage") else None,
            text=response.text,
            segments=response.segments or [],
            language=response.language,
            duration=response.duration,
            audio_file=audio_path,
            model_name=options.model,
            transcription_timestamp=datetime.now(),
        )

        logger.info(
            dedent(f"""
                Successfully transcribed {audio_path.name}:
                - Characters: {len(transcription_result.text)}
                - Segments: {len(transcription_result.segments)}
                - Language: {transcription_result.language}
            """).strip()
        )

        return transcription_result

    except WhisperError:
        raise
    except AudioFileError:
        raise
    except Exception as e:
        raise TranscriptionError(
            f"API transcription failed for {audio_path.name}: {e}", str(audio_path)
        ) from e
