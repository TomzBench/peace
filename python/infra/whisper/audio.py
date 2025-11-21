from pathlib import Path

from .exceptions import AudioFileError
from .models import AudioFile

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def open_audio_file(path: Path) -> AudioFile:
    """Open and read audio file, returning AudioFile with metadata.

    Args:
        path: Path to audio file

    Returns:
        AudioFile with file contents and metadata

    Raises:
        AudioFileError: If file is invalid or unsupported
    """
    if not path.exists():
        raise AudioFileError(f"Audio file not found: {path}", str(path))
    if not path.is_file():
        raise AudioFileError(f"Path is not a file: {path}", str(path))

    file_stat = path.stat()
    if file_stat.st_size > MAX_FILE_SIZE_BYTES:
        raise AudioFileError(
            f"OpenAI API limit of {MAX_FILE_SIZE_MB}MB",
            str(path),
        )

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
