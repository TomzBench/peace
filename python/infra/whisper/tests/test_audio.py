"""Tests for audio file utilities."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ..audio import MAX_FILE_SIZE_BYTES, open_audio_file
from ..exceptions import AudioFileError
from ..models import AudioFile


def test_open_audio_file_success(tmp_path: Path) -> None:
    """Test successfully opening a valid audio file."""
    audio_file = tmp_path / "test.mp3"
    test_data = b"fake mp3 data"
    audio_file.write_bytes(test_data)

    result = open_audio_file(audio_file)

    assert isinstance(result, AudioFile)
    assert result.data == test_data
    assert result.path == audio_file
    assert result.size == len(test_data)
    assert result.extension == ".mp3"
    assert result.filename == "test.mp3"


def test_open_audio_file_file_not_found() -> None:
    """Test that missing file raises AudioFileError."""
    non_existent = Path("/nonexistent/file.mp3")

    with pytest.raises(AudioFileError) as exc_info:
        open_audio_file(non_existent)

    assert "Audio file not found" in str(exc_info.value)
    assert exc_info.value.file_path == str(non_existent)


def test_open_audio_file_is_directory(tmp_path: Path) -> None:
    """Test that directory path raises AudioFileError."""
    audio_dir = tmp_path / "audio_dir"
    audio_dir.mkdir()

    with pytest.raises(AudioFileError) as exc_info:
        open_audio_file(audio_dir)

    assert "Path is not a file" in str(exc_info.value)


def test_open_audio_file_exceeds_size_limit(tmp_path: Path) -> None:
    """Test that file exceeding 25MB limit raises AudioFileError."""
    large_file = tmp_path / "large.mp3"
    large_file.write_bytes(b"data")

    # Mock stat to return size > 25MB (avoid creating large file)
    with patch.object(Path, "stat") as mock_stat:
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = 0o100644  # Regular file mode
        mock_stat_result.st_size = MAX_FILE_SIZE_BYTES + 1
        mock_stat.return_value = mock_stat_result

        with pytest.raises(AudioFileError) as exc_info:
            open_audio_file(large_file)

        assert "OpenAI API limit of 25MB" in str(exc_info.value)


def test_open_audio_file_invalid_extension(tmp_path: Path) -> None:
    """Test that invalid file extension raises AudioFileError."""
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_bytes(b"text data")

    with pytest.raises(AudioFileError) as exc_info:
        open_audio_file(invalid_file)

    assert "unsupported audio ext" in str(exc_info.value)


@pytest.mark.parametrize(
    "extension",
    [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".webm", ".mp4"],
)
def test_open_audio_file_valid_extensions(tmp_path: Path, extension: str) -> None:
    """Test that all valid audio extensions are accepted."""
    audio_file = tmp_path / f"test{extension}"
    test_data = b"audio data"
    audio_file.write_bytes(test_data)

    result = open_audio_file(audio_file)

    assert isinstance(result, AudioFile)
    assert result.data == test_data
    assert result.extension == extension


def test_open_audio_file_case_insensitive_extension(tmp_path: Path) -> None:
    """Test that file extension check is case-insensitive."""
    audio_file = tmp_path / "test.MP3"
    test_data = b"audio data"
    audio_file.write_bytes(test_data)

    result = open_audio_file(audio_file)

    assert isinstance(result, AudioFile)
    assert result.data == test_data
    assert result.extension == ".mp3"  # Normalized to lowercase


def test_open_audio_file_returns_complete_data(tmp_path: Path) -> None:
    """Test that entire file contents are returned."""
    audio_file = tmp_path / "test.mp3"
    # Create file with known size
    test_data = b"x" * 1000  # 1KB of data
    audio_file.write_bytes(test_data)

    result = open_audio_file(audio_file)

    assert isinstance(result, AudioFile)
    assert len(result.data) == 1000
    assert result.data == test_data
    assert result.size == 1000
