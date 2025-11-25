import asyncio
from io import BytesIO
from math import ceil
from pathlib import Path

from pydub import AudioSegment  # type: ignore[import-untyped]

from .exceptions import AudioFileError
from .models import AudioFile, AudioFileChunk

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def open_audio_file(path: Path) -> AudioFile:
    """Open and read audio file, returning AudioFile with metadata.

    Raises AudioFileError.
    """
    if not path.exists():
        raise AudioFileError(f"Audio file not found: {path}", str(path))
    if not path.is_file():
        raise AudioFileError(f"Path is not a file: {path}", str(path))

    file_stat = path.stat()
    # Note: Don't reject large files here - chunking will handle them
    # If file > 25MB, transcribe_audio will automatically chunk it

    ext = path.suffix.lower()
    valid_extensions = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".webm", ".mp4"}
    if ext not in valid_extensions:
        raise AudioFileError(f"unsupported audio ext: {ext}")

    with open(path, "rb") as f:
        data = f.read()

    return AudioFile(
        path=path,
        data=data,
        size=file_stat.st_size,
        extension=ext,
        filename=path.name,
    )


async def open_audio_file_async(path: Path) -> AudioFile:
    """Open and read audio file asynchronously.

    Raises AudioFileError.
    """
    return await asyncio.to_thread(open_audio_file, path)


def chunk_audio_file(
    audio_file: AudioFile,
    chunk_duration_ms: int = 300000,  # 5 minutes default
) -> list[AudioFileChunk]:
    """Split audio into time-based chunks in-memory.

    Raises AudioFileError.
    """
    try:
        # Load audio from bytes
        # Remove leading dot from extension for pydub format parameter
        audio_format = audio_file.extension.lstrip(".")
        audio_segment = AudioSegment.from_file(
            BytesIO(audio_file.data), format=audio_format
        )

        # Get total duration and calculate number of chunks
        total_duration_ms = len(audio_segment)
        total_chunks = ceil(total_duration_ms / chunk_duration_ms)

        # Create chunks using traditional for loop
        base_filename = audio_file.filename.rsplit(".", 1)[0]  # Remove extension
        chunks = []

        for chunk_index in range(total_chunks):
            # Calculate time boundaries
            start_ms = chunk_index * chunk_duration_ms
            end_ms = min((chunk_index + 1) * chunk_duration_ms, total_duration_ms)

            # Slice audio segment
            chunk_segment = audio_segment[start_ms:end_ms]

            # Export chunk to bytes in-memory
            chunk_buffer = BytesIO()
            chunk_segment.export(chunk_buffer, format=audio_format)
            chunk_data = chunk_buffer.getvalue()

            # Generate chunk filename
            chunk_filename = f"{base_filename}_chunk_{chunk_index}{audio_file.extension}"

            # Create and append AudioFileChunk
            chunk = AudioFileChunk(
                filename=chunk_filename,
                data=chunk_data,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                start_time_ms=start_ms,
                end_time_ms=end_ms,
                original_filename=audio_file.filename,
                original_path=audio_file.path,
            )
            chunks.append(chunk)

        return chunks

    except Exception as e:
        raise AudioFileError(
            f"Failed to chunk audio file {audio_file.filename}: {e}",
            str(audio_file.path),
        ) from e
