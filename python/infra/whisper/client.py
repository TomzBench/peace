"""Functional wrapper for OpenAI Whisper transcription."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import whisper

from python.infra.whisper.exceptions import (
    AudioFileError,
    ModelLoadError,
    TranscriptionError,
)
from python.infra.whisper.models import (
    Segment,
    TranscriptionOptions,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)

# Cache loaded models to avoid reloading
_model_cache: dict[str, Any] = {}


def load_model(model_name: str = "base") -> Any:
    """Load a Whisper model, with caching.

    Args:
        model_name: Name of the Whisper model (tiny, base, small, medium, large)

    Returns:
        Loaded Whisper model

    Raises:
        ModelLoadError: If model fails to load

    Examples:
        >>> model = load_model("base")
        >>> model = load_model("small")
    """
    if model_name in _model_cache:
        logger.debug(f"Using cached model: {model_name}")
        return _model_cache[model_name]

    logger.info(f"Loading Whisper model: {model_name}")

    try:
        model = whisper.load_model(model_name)
        _model_cache[model_name] = model
        logger.info(f"Successfully loaded model: {model_name}")
        return model
    except Exception as e:
        raise ModelLoadError(f"Failed to load model '{model_name}': {e}", model_name) from e


def _validate_audio_file(audio_path: Path) -> None:
    """Validate that audio file exists and is readable.

    Args:
        audio_path: Path to audio file

    Raises:
        AudioFileError: If file is invalid or missing
    """
    if not audio_path.exists():
        raise AudioFileError(f"Audio file not found: {audio_path}", str(audio_path))

    if not audio_path.is_file():
        raise AudioFileError(f"Path is not a file: {audio_path}", str(audio_path))

    # Check file extension
    valid_extensions = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".webm", ".mp4"}
    if audio_path.suffix.lower() not in valid_extensions:
        logger.warning(
            f"Audio file has unusual extension: {audio_path.suffix}. "
            f"Whisper supports: {', '.join(sorted(valid_extensions))}"
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
    options: TranscriptionOptions | None = None,
) -> TranscriptionResult:
    """Transcribe audio file using Whisper.

    Args:
        audio_path: Path to audio file (mp3, wav, m4a, etc.)
        options: Transcription options (model, language, task, etc.)

    Returns:
        TranscriptionResult with full text, segments, and metadata

    Raises:
        AudioFileError: If audio file is invalid or missing
        ModelLoadError: If Whisper model fails to load
        TranscriptionError: If transcription fails

    Examples:
        >>> from pathlib import Path
        >>> result = transcribe_audio(Path("audio.mp3"))
        >>> print(f"Detected language: {result.language}")
        >>> print(f"Text: {result.text}")

        >>> opts = TranscriptionOptions(model="small", language="en")
        >>> result = transcribe_audio(Path("audio.mp3"), opts)
    """
    options = options or TranscriptionOptions()
    audio_path = Path(audio_path)

    logger.info(f"Transcribing audio file: {audio_path}")

    # Validate audio file
    _validate_audio_file(audio_path)

    # Load model
    try:
        model = load_model(options.model)
    except ModelLoadError:
        raise

    # Prepare transcription arguments
    transcribe_kwargs: dict[str, Any] = {
        "task": options.task,
        "temperature": options.temperature,
        "condition_on_previous_text": options.condition_on_previous_text,
        "fp16": options.fp16,
        "verbose": options.verbose,
    }

    # Add optional parameters if provided
    if options.language:
        transcribe_kwargs["language"] = options.language
    if options.best_of is not None:
        transcribe_kwargs["best_of"] = options.best_of
    if options.beam_size is not None:
        transcribe_kwargs["beam_size"] = options.beam_size
    if options.patience is not None:
        transcribe_kwargs["patience"] = options.patience
    if options.length_penalty is not None:
        transcribe_kwargs["length_penalty"] = options.length_penalty
    if options.initial_prompt:
        transcribe_kwargs["initial_prompt"] = options.initial_prompt
    if options.compression_ratio_threshold is not None:
        transcribe_kwargs["compression_ratio_threshold"] = options.compression_ratio_threshold
    if options.logprob_threshold is not None:
        transcribe_kwargs["logprob_threshold"] = options.logprob_threshold
    if options.no_speech_threshold is not None:
        transcribe_kwargs["no_speech_threshold"] = options.no_speech_threshold

    # Merge with additional kwargs
    transcribe_kwargs.update(options.whisper_kwargs)

    # Perform transcription
    try:
        result = model.transcribe(str(audio_path), **transcribe_kwargs)

        # Parse segments
        segments = _parse_segments(result.get("segments", []))

        # Build transcription result
        transcription_result = TranscriptionResult(
            text=result["text"],
            segments=segments,
            language=result.get("language", "unknown"),
            audio_file=audio_path,
            model_name=options.model,
            transcription_timestamp=datetime.now(),
            duration=result.get("duration"),
        )

        logger.info(
            f"Successfully transcribed {audio_path.name}: "
            f"{len(transcription_result.text)} chars, "
            f"{len(segments)} segments, "
            f"language={transcription_result.language}"
        )

        return transcription_result

    except Exception as e:
        raise TranscriptionError(
            f"Transcription failed for {audio_path.name}: {e}", str(audio_path)
        ) from e


def transcribe_and_translate(
    audio_path: Path,
    options: TranscriptionOptions | None = None,
) -> TranscriptionResult:
    """Transcribe and translate audio to English using Whisper.

    This is a convenience function that sets task="translate" automatically.

    Args:
        audio_path: Path to audio file
        options: Transcription options (task will be overridden to "translate")

    Returns:
        TranscriptionResult with English translation in the text field

    Raises:
        AudioFileError: If audio file is invalid or missing
        ModelLoadError: If Whisper model fails to load
        TranscriptionError: If transcription fails

    Examples:
        >>> result = transcribe_and_translate(Path("spanish_audio.mp3"))
        >>> print(f"English translation: {result.text}")
    """
    options = options or TranscriptionOptions()
    options.task = "translate"

    logger.info(f"Transcribing and translating to English: {audio_path}")

    result = transcribe_audio(audio_path, options)

    # Store translation separately for clarity
    result.translation = result.text

    return result
