"""Functional wrapper for OpenAI Whisper API transcription."""

import logging
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any

from openai import OpenAI

from python.config.settings import get_settings
from python.infra.whisper.exceptions import (
    AudioFileError,
    TranscriptionError,
    WhisperError,
)
from python.infra.whisper.models import (
    Segment,
    TranscriptionApiOptions,
    TranscriptionResult,
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

    Examples:
        >>> client = _get_client()
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


def _parse_segments(segments_data: list[dict[str, Any]]) -> list[Segment]:
    """Parse Whisper segment data into Segment models.

    Args:
        segments_data: Raw segment list from Whisper

    Returns:
        List of Segment models
    """
    segments = []
    for seg in segments_data:
        try:
            segments.append(
                Segment(
                    id=seg["id"],
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"],
                    tokens=seg["tokens"],
                    temperature=seg["temperature"],
                    avg_logprob=seg["avg_logprob"],
                    compression_ratio=seg["compression_ratio"],
                    no_speech_prob=seg["no_speech_prob"],
                )
            )
        except Exception as e:
            logger.warning(f"Failed to parse segment {seg.get('id')}: {e}")
            continue
    return segments


def transcribe_audio(
    audio_path: Path,
    options: TranscriptionApiOptions | None = None,
) -> TranscriptionResult:
    """Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_path: Path to audio file (mp3, wav, m4a, etc.) - max 25MB
        options: API transcription options (language, temperature, initial_prompt)

    Returns:
        TranscriptionResult with full text, segments, and metadata

    Raises:
        AudioFileError: If audio file is invalid, missing, or exceeds 25MB
        WhisperError: If API key is not configured
        TranscriptionError: If transcription fails

    Examples:
        >>> from pathlib import Path
        >>> result = transcribe_audio(Path("audio.mp3"))
        >>> print(f"Detected language: {result.language}")
        >>> print(f"Text: {result.text}")

        >>> opts = TranscriptionApiOptions(language="en", temperature=0.2)
        >>> result = transcribe_audio(Path("audio.mp3"), opts)

    Note:
        OpenAI API only supports the "whisper-1" model. Advanced parameters
        (beam_size, best_of, etc.) are only available with TranscriptionLocalOptions
        when running Whisper locally.
    """
    options = options or TranscriptionApiOptions()
    audio_path = Path(audio_path)

    logger.info(f"Transcribing audio file via OpenAI API: {audio_path}")

    # Validate audio file (includes size check)
    _validate_audio_file(audio_path)

    # Get OpenAI client
    try:
        client = _get_client()
    except WhisperError:
        raise

    # Prepare API parameters (only supported ones)
    api_params: dict[str, Any] = {
        "model": "whisper-1",  # Only model available
        "response_format": "verbose_json",  # Get segments and metadata
    }

    # Add optional parameters supported by API
    if options.language:
        api_params["language"] = options.language
    if options.temperature != 0.0:
        api_params["temperature"] = options.temperature
    if options.initial_prompt:
        api_params["prompt"] = options.initial_prompt  # Note: renamed from initial_prompt

    # Perform transcription
    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                file=audio_file,
                **api_params,
            )

        # Parse segments from response
        segments = _parse_segments(response.segments or [])

        # Build transcription result
        transcription_result = TranscriptionResult(
            text=response.text,
            segments=segments,
            language=response.language,
            audio_file=audio_path,
            model_name="whisper-1",
            transcription_timestamp=datetime.now(),
            duration=response.duration,
        )

        logger.info(
            dedent(f"""
                Successfully transcribed {audio_path.name}:
                {len(transcription_result.text)} chars,
                {len(segments)} segments,
                language={transcription_result.language}
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


def transcribe_and_translate(
    audio_path: Path,
    options: TranscriptionApiOptions | None = None,
) -> TranscriptionResult:
    """Transcribe and translate audio to English using OpenAI Whisper API.

    Uses the separate translations endpoint which transcribes non-English audio
    and translates it to English in a single step.

    Args:
        audio_path: Path to audio file - max 25MB
        options: API transcription options (temperature, initial_prompt)

    Returns:
        TranscriptionResult with English translation in the text field

    Raises:
        AudioFileError: If audio file is invalid, missing, or exceeds 25MB
        WhisperError: If API key is not configured
        TranscriptionError: If translation fails

    Examples:
        >>> result = transcribe_and_translate(Path("spanish_audio.mp3"))
        >>> print(f"English translation: {result.text}")

    Note:
        The language parameter is not used for translation - the API automatically
        detects the source language and translates to English.
    """
    options = options or TranscriptionApiOptions()
    audio_path = Path(audio_path)

    logger.info(f"Transcribing and translating to English via OpenAI API: {audio_path}")

    # Validate audio file (includes size check)
    _validate_audio_file(audio_path)

    # Get OpenAI client
    try:
        client = _get_client()
    except WhisperError:
        raise

    # Prepare API parameters (only supported ones)
    api_params: dict[str, Any] = {
        "model": "whisper-1",
        "response_format": "verbose_json",
    }

    # Add optional parameters supported by API
    if options.temperature != 0.0:
        api_params["temperature"] = options.temperature
    if options.initial_prompt:
        api_params["prompt"] = options.initial_prompt

    # Perform translation
    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.translations.create(
                file=audio_file,
                **api_params,
            )

        # Parse segments from response
        segments = _parse_segments(response.segments or [])

        # Build transcription result
        transcription_result = TranscriptionResult(
            text=response.text,
            segments=segments,
            language=response.language,
            audio_file=audio_path,
            model_name="whisper-1",
            transcription_timestamp=datetime.now(),
            duration=response.duration,
            translation=response.text,  # Store translation
        )

        logger.info(
            dedent(f"""
                Successfully translated {audio_path.name} to English:
                {len(transcription_result.text)} chars,
                {len(segments)} segments
            """).strip()
        )

        return transcription_result

    except WhisperError:
        raise
    except AudioFileError:
        raise
    except Exception as e:
        raise TranscriptionError(
            f"API translation failed for {audio_path.name}: {e}", str(audio_path)
        ) from e
