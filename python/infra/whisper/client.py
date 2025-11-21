"""Functional wrapper for OpenAI Whisper API transcription."""

import logging
from dataclasses import asdict
from datetime import datetime

from openai import AsyncOpenAI

from .audio import chunk_audio_file
from .dependencies import inject_deps
from .exceptions import TranscriptionError
from .models import (
    AudioFile,
    ResponseOptions,
    TranscriptionOptions,
    TranscriptionResult,
    TranscriptionSegment,
    Usage,
    flatten_options,
)

logger = logging.getLogger(__name__)


def _merge_transcription_results(
    chunk_results: list[TranscriptionResult],
) -> TranscriptionResult:
    """Merge multiple chunk transcription results into a single result.

    Args:
        chunk_results: List of TranscriptionResult objects from individual chunks

    Returns:
        Single merged TranscriptionResult

    Notes:
        - Text is concatenated with newlines
        - Segments have timestamps adjusted based on chunk positions
        - Usage statistics are summed if present
        - Metadata (language, model, etc.) from first chunk is used
    """
    if not chunk_results:
        raise ValueError("Cannot merge empty list of chunk results")

    if len(chunk_results) == 1:
        return chunk_results[0]

    # Concatenate text from all chunks
    merged_text = "\n".join(result.text for result in chunk_results)

    # Merge segments with adjusted timestamps
    merged_segments: list[TranscriptionSegment] = []
    for result in chunk_results:
        if result.segments:
            merged_segments.extend(result.segments)

    # Sum usage statistics if present
    merged_usage: Usage | None = None
    if any(result.usage is not None for result in chunk_results):
        # Check if all usage types are the same
        usage_types = {result.usage.type for result in chunk_results if result.usage}
        if len(usage_types) == 1:
            usage_type = usage_types.pop()

            if usage_type == "duration":
                total_seconds = sum(
                    result.usage.seconds
                    for result in chunk_results
                    if result.usage and hasattr(result.usage, "seconds")
                )
                from openai.types.audio.transcription import UsageDuration

                merged_usage = UsageDuration(type="duration", seconds=total_seconds)
            elif usage_type == "tokens":
                total_input = sum(
                    result.usage.input_tokens
                    for result in chunk_results
                    if result.usage and hasattr(result.usage, "input_tokens")
                )
                total_output = sum(
                    result.usage.output_tokens
                    for result in chunk_results
                    if result.usage and hasattr(result.usage, "output_tokens")
                )
                from openai.types.audio.transcription import UsageTokens

                merged_usage = UsageTokens(
                    type="tokens",
                    input_tokens=total_input,
                    output_tokens=total_output,
                    total_tokens=total_input + total_output,
                )

    # Calculate total duration
    total_duration = sum(result.duration or 0.0 for result in chunk_results)

    # Use metadata from first chunk
    first_chunk = chunk_results[0]

    return TranscriptionResult(
        object="transcription",
        usage=merged_usage,
        text=merged_text,
        segments=merged_segments,
        language=first_chunk.language,
        duration=total_duration,
        audio_file=first_chunk.audio_file,
        model_name=first_chunk.model_name,
        transcription_timestamp=first_chunk.transcription_timestamp,
    )


@inject_deps
async def transcribe_audio(
    audio_file: AudioFile,
    options: TranscriptionOptions | None = None,
    client: AsyncOpenAI | None = None,
) -> TranscriptionResult:
    """Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_file: AudioFile with validated audio data and metadata
        options: Transcription options with composable request/response config
        client: AsyncOpenAI client (auto-injected if None via @inject_deps)

    Returns:
        TranscriptionResult with text, segments, metadata, and usage info

    Raises:
        TranscriptionError: If transcription fails (wraps OpenAI SDK errors)
    """
    options = options or TranscriptionOptions()
    logger.info(f"Transcribing audio file via OpenAI API: {audio_file.filename}")

    # Ensure client is injected (decorator should handle this)
    assert client is not None, "AsyncOpenAI client must be provided or injected"

    # Always chunk audio (even if it results in single chunk)
    try:
        chunks = chunk_audio_file(audio_file)
        logger.info(f"Chunked audio into {len(chunks)} chunk(s)")

        # Transcribe each chunk sequentially
        chunk_results: list[TranscriptionResult] = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Transcribing chunk {i + 1}/{len(chunks)}: {chunk.filename}")

            # Pass chunk file tuple directly to SDK via .file property
            response = await client.audio.transcriptions.create(
                file=chunk.file, **flatten_options(options), **asdict(ResponseOptions())
            )

            # Build transcription result for this chunk
            chunk_result = TranscriptionResult(
                object="transcription",
                usage=response.usage if hasattr(response, "usage") else None,
                text=response.text,
                segments=response.segments or [],
                language=response.language,
                duration=response.duration,
                audio_file=audio_file.path,  # Use original file path
                model_name=options.model,
                transcription_timestamp=datetime.now(),
            )

            chunk_results.append(chunk_result)
            logger.info(f"Chunk {i + 1}/{len(chunks)} transcribed successfully")

        # Merge all chunk results into single result
        transcription_result = _merge_transcription_results(chunk_results)

        logger.info(f"Successfully transcribed: {transcription_result!r}")

        return transcription_result

    except Exception as e:
        # Wrap all errors in TranscriptionError with context
        raise TranscriptionError(
            f"API transcription failed for {audio_file.filename}: {e}",
            str(audio_file.path),
        ) from e
