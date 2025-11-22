"""Tests for multi-chunk transcription with pipeline merging."""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai.types.audio.transcription import UsageDuration

from python.infra.whisper.client import transcribe_audio
from python.infra.whisper.models import (
    AudioFile,
    AudioFileChunk,
    TranscriptionSegment,
)


def make_mock_chunk(idx: int, start: int, dur: int) -> AudioFileChunk:
    """Create a mock audio chunk."""
    name = f"test_chunk_{idx}.mp3"
    data = f"fake audio data {idx}".encode()
    return AudioFileChunk(
        filename=name,
        data=data,
        chunk_index=idx,
        total_chunks=3,
        start_time_ms=start,
        end_time_ms=start + dur,
        original_filename="test.mp3",
        original_path=Path("/fake/test.mp3"),
    )


def make_mock_segment(n: int, offset: float = 0.0) -> TranscriptionSegment:
    """Create a mock transcription segment."""
    return TranscriptionSegment(
        id=n,
        seek=0,
        start=offset + n * 5.0,
        end=offset + (n + 1) * 5.0,
        text=f"segment {n}",
        tokens=[n * 10, n * 10 + 1],
        temperature=0.0,
        avg_logprob=-0.2,
        compression_ratio=1.5,
        no_speech_prob=0.01,
    )


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_multiple_chunks_merged_in_pipeline(
    mock_chunk_audio_file: MagicMock,
) -> None:
    """Test that multiple chunks are transcribed and merged within the RxPY pipeline."""
    # Create AudioFile
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create 3 mock chunks
    chunks = [
        make_mock_chunk(0, 0, 10000),  # 10 seconds
        make_mock_chunk(1, 10000, 10000),  # 10 seconds
        make_mock_chunk(2, 20000, 5000),  # 5 seconds
    ]
    mock_chunk_audio_file.return_value = chunks

    # Mock AsyncOpenAI client with different responses for each chunk
    mock_client = MagicMock()

    # Create mock responses for each chunk
    mock_responses = []
    for i in range(3):
        mock_response = MagicMock()
        mock_response.text = f"Chunk {i} text"
        mock_response.language = "en"
        mock_response.duration = [10.0, 10.0, 5.0][i]
        mock_response.segments = [make_mock_segment(i * 2), make_mock_segment(i * 2 + 1)]
        mock_response.usage = UsageDuration(type="duration", seconds=mock_response.duration)
        mock_responses.append(mock_response)

    # Set up the mock to return different responses for each call
    mock_client.audio.transcriptions.create = AsyncMock(side_effect=mock_responses)

    # Execute transcription
    result = await transcribe_audio(audio_file, client=mock_client, max_concurrent=2)

    # Verify the result is properly merged
    assert result.text == "Chunk 0 text\nChunk 1 text\nChunk 2 text"
    assert result.language == "en"
    assert result.duration == 25.0  # Sum of all durations
    assert len(result.segments) == 6  # 2 segments per chunk
    assert result.usage is not None
    assert result.usage.type == "duration"
    # Sum of all usage durations
    assert hasattr(result.usage, "seconds") and result.usage.seconds == 25.0

    # Verify all chunks were transcribed
    assert mock_client.audio.transcriptions.create.call_count == 3

    # Verify segments are in order
    for i, segment in enumerate(result.segments):
        assert segment.text == f"segment {i}"


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_chunks_processed_in_order(
    mock_chunk_audio_file: MagicMock,
) -> None:
    """Test that chunks are merged in the correct order even if processed out of order."""
    # Create AudioFile
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create 5 mock chunks
    chunks = [make_mock_chunk(i, i * 5000, 5000) for i in range(5)]
    mock_chunk_audio_file.return_value = chunks

    # Mock AsyncOpenAI client
    mock_client = MagicMock()

    # Track the order in which chunks are processed
    process_order = []

    async def mock_transcribe(file: tuple[str, bytes], **kwargs: Any) -> MagicMock:
        # Extract chunk index from the file tuple's filename
        filename = file[0]  # file is a tuple (filename, data)
        chunk_idx = int(filename.split("_")[2].split(".")[0])  # Extract from "test_chunk_X.mp3"
        process_order.append(chunk_idx)

        # Create response for this chunk
        mock_response = MagicMock()
        mock_response.text = f"Text from chunk {chunk_idx}"
        mock_response.language = "en"
        mock_response.duration = 5.0
        mock_response.segments = []
        mock_response.usage = None
        return mock_response

    mock_client.audio.transcriptions.create = mock_transcribe

    # Execute with max_concurrent=2 to allow out-of-order processing
    result = await transcribe_audio(
        audio_file,
        client=mock_client,
        max_concurrent=2,
    )

    # Verify the text is in the correct order regardless of processing order
    expected_text = "\n".join(f"Text from chunk {i}" for i in range(5))
    assert result.text == expected_text

    # Verify all chunks were processed
    assert len(process_order) == 5


@pytest.mark.asyncio
@patch("python.infra.whisper.client.chunk_audio_file")
async def test_transcribe_audio_single_chunk_no_merge(
    mock_chunk_audio_file: MagicMock,
) -> None:
    """Test that single chunk is handled correctly without merging."""
    # Create AudioFile
    audio_data = b"fake audio data"
    audio_file = AudioFile(
        path=Path("/fake/test.mp3"),
        data=audio_data,
        size=len(audio_data),
        extension=".mp3",
        filename="test.mp3",
    )

    # Create single mock chunk
    chunks = [make_mock_chunk(0, 0, 10000)]
    mock_chunk_audio_file.return_value = chunks

    # Mock AsyncOpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Single chunk text"
    mock_response.language = "en"
    mock_response.duration = 10.0
    mock_response.segments = [make_mock_segment(0)]
    mock_response.usage = UsageDuration(type="duration", seconds=10.0)

    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    # Execute transcription
    result = await transcribe_audio(audio_file, client=mock_client)

    # Verify the result (should be essentially the same as the single chunk)
    assert result.text == "Single chunk text"
    assert result.language == "en"
    assert result.duration == 10.0
    assert len(result.segments) == 1
    assert result.usage is not None
    assert hasattr(result.usage, "seconds") and result.usage.seconds == 10.0

    # Verify only one API call was made
    assert mock_client.audio.transcriptions.create.call_count == 1
