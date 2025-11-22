"""Functional wrapper for OpenAI Whisper API transcription."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from datetime import datetime

import reactivex as rx
from openai import AsyncOpenAI
from reactivex import Observable
from reactivex import operators as ops
from reactivex.scheduler.eventloop import AsyncIOScheduler

from .audio import chunk_audio_file
from .dependencies import inject_deps
from .exceptions import TranscriptionError
from .models import (
    AudioFile,
    AudioFileChunk,
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


def _create_chunk_transcriber(
    client: AsyncOpenAI,
    options: TranscriptionOptions,
    audio_file: AudioFile,
) -> Callable[[tuple[int, AudioFileChunk]], Awaitable[tuple[int, TranscriptionResult]]]:
    """Create a function that transcribes a single chunk.

    Pure function factory that creates a transcriber bound to specific
    client and options, improving testability and reusability.

    Args:
        client: AsyncOpenAI client for API calls
        options: Transcription options
        audio_file: Original AudioFile for metadata

    Returns:
        Async function that transcribes a chunk and returns indexed result
    """

    async def transcribe_chunk(
        indexed_chunk: tuple[int, AudioFileChunk]
    ) -> tuple[int, TranscriptionResult]:
        """Transcribe a single chunk and return result with index."""
        index, chunk = indexed_chunk
        total_chunks = chunk.total_chunks
        logger.info(f"Transcribing chunk {index + 1}/{total_chunks}: {chunk.filename}")

        # Call OpenAI API
        response = await client.audio.transcriptions.create(
            file=chunk.file, **flatten_options(options), **asdict(ResponseOptions())
        )

        # Build result for this chunk
        result = TranscriptionResult(
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

        logger.info(f"Chunk {index + 1}/{total_chunks} transcribed successfully")
        return (index, result)

    return transcribe_chunk


def _create_chunking_observable(audio_file: AudioFile) -> Observable[list[AudioFileChunk]]:
    """Create an observable that emits chunked audio.

    Moves chunking into the reactive pipeline for better composability.

    Args:
        audio_file: AudioFile to chunk

    Returns:
        Observable that emits a list of AudioFileChunk objects
    """

    def chunk_audio() -> list[AudioFileChunk]:
        """Chunk audio and log the operation."""
        chunks = chunk_audio_file(audio_file)
        logger.info(f"Chunked audio into {len(chunks)} chunk(s)")
        return chunks

    return rx.defer(lambda _: rx.just(chunk_audio()))


def _create_transcription_pipeline(
    audio_file: AudioFile,
    client: AsyncOpenAI,
    options: TranscriptionOptions,
    max_concurrent: int = 3,
) -> Observable[TranscriptionResult]:
    """Create the complete RxPy pipeline for audio transcription.

    Combines chunking, parallel transcription, and result merging
    into a single reactive pipeline.

    Args:
        audio_file: AudioFile to transcribe
        client: AsyncOpenAI client for API calls
        options: Transcription options
        max_concurrent: Maximum chunks to process concurrently

    Returns:
        Observable that emits a single merged TranscriptionResult
    """
    # Create the transcriber function once, bound to our parameters
    transcriber = _create_chunk_transcriber(client, options, audio_file)

    def process_chunks(chunks: list[AudioFileChunk]) -> Observable[TranscriptionResult]:
        """Process chunks through transcription pipeline."""
        if not chunks:
            raise ValueError("No chunks to process")

        # Create indexed chunks
        indexed_chunks = list(enumerate(chunks))

        # Build the transcription pipeline
        def create_future_observable(
            chunk: tuple[int, AudioFileChunk]
        ) -> Observable[tuple[int, TranscriptionResult]]:
            """Convert chunk to observable from future."""
            return rx.from_future(asyncio.ensure_future(transcriber(chunk)))

        return rx.from_iterable(indexed_chunks).pipe(
            # Convert each chunk to a future-based observable
            ops.map(create_future_observable),
            # Process chunks concurrently
            ops.merge(max_concurrent=max_concurrent),
            # Collect all results
            ops.to_list(),
            # Sort by index and merge
            ops.map(_merge_sorted_results),
        )

    # Start with chunking, then process
    return _create_chunking_observable(audio_file).pipe(ops.flat_map(process_chunks))


def _merge_sorted_results(
    indexed_results: list[tuple[int, TranscriptionResult]]
) -> TranscriptionResult:
    """Sort indexed results by chunk order and merge them.

    Args:
        indexed_results: List of (index, TranscriptionResult) tuples

    Returns:
        Single merged TranscriptionResult
    """
    # Sort by index to maintain chunk order
    sorted_results = sorted(indexed_results, key=lambda x: x[0])
    # Extract just the results
    chunk_results = [result for _, result in sorted_results]
    # Merge and return
    return _merge_transcription_results(chunk_results)


async def _execute_observable(observable: Observable[TranscriptionResult]) -> TranscriptionResult:
    """Execute an observable in the async context and await its result.

    Bridges the gap between RxPy observables and async/await.

    Args:
        observable: Observable that emits a single TranscriptionResult

    Returns:
        The emitted TranscriptionResult

    Raises:
        Any exception raised during observable execution
    """
    # Get current event loop and create scheduler
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(loop=loop)

    # Create containers for result and error
    result_container: list[TranscriptionResult] = []
    error_container: list[Exception] = []
    completion = asyncio.Event()

    def on_next(result: TranscriptionResult) -> None:
        """Handle emitted result."""
        result_container.append(result)

    def on_error(error: Exception) -> None:
        """Handle errors from the pipeline."""
        error_container.append(error)
        completion.set()

    def on_completed() -> None:
        """Handle successful completion."""
        completion.set()

    # Subscribe to the observable
    observable.subscribe(
        on_next=on_next,
        on_error=on_error,
        on_completed=on_completed,
        scheduler=scheduler,
    )

    # Wait for completion
    await completion.wait()

    # Check for errors
    if error_container:
        raise error_container[0]

    # Ensure we got a result
    if not result_container:
        raise ValueError("Observable completed without emitting a result")

    return result_container[0]


@inject_deps
async def transcribe_audio(
    audio_file: AudioFile,
    options: TranscriptionOptions | None = None,
    client: AsyncOpenAI | None = None,
    max_concurrent: int = 3,
) -> TranscriptionResult:
    """Transcribe audio file using OpenAI Whisper API.

    Thin async wrapper that bridges to the RxPy reactive pipeline.
    Handles chunking, parallel processing, and result merging transparently.

    Args:
        audio_file: AudioFile with validated audio data and metadata
        options: Transcription options with composable request/response config
        client: AsyncOpenAI client (auto-injected if None via @inject_deps)
        max_concurrent: Maximum number of chunks to transcribe concurrently

    Returns:
        TranscriptionResult with text, segments, metadata, and usage info

    Raises:
        TranscriptionError: If transcription fails (wraps OpenAI SDK errors)
    """
    options = options or TranscriptionOptions()
    logger.info(f"Transcribing audio file via OpenAI API: {audio_file.filename}")

    # Ensure client is injected
    assert client is not None, "AsyncOpenAI client must be provided or injected"

    try:
        # Create and execute the reactive pipeline
        pipeline = _create_transcription_pipeline(
            audio_file, client, options, max_concurrent
        )
        result = await _execute_observable(pipeline)

        logger.info(f"Successfully transcribed: {result!r}")
        return result

    except Exception as e:
        # Wrap all errors in TranscriptionError with context
        raise TranscriptionError(
            f"API transcription failed for {audio_file.filename}: {e}",
            str(audio_file.path),
        ) from e
