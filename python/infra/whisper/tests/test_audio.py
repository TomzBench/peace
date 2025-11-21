"""Tests for audio file utilities."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ..audio import MAX_FILE_SIZE_BYTES, chunk_audio_file, open_audio_file
from ..exceptions import AudioFileError
from ..models import AudioFile, AudioFileChunk


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


# Tests for chunk_audio_file
#
# NOTE: These are unit tests with mocked audio processing for speed.
# Real audio processing is tested in integration tests (see update_fixtures.py).
#
# Integration tests TODO:
# - Generate test audio fixtures using update_fixtures.py
# - Add integration test suite that uses real audio files
# - Verify pydub integration and chunk validity with real audio
#


def test_chunk_audio_file_multiple_chunks(tmp_path: Path) -> None:
    """Test chunking creates multiple chunks for long audio."""
    audio_path = tmp_path / "long_audio.mp3"
    audio_path.write_bytes(b"fake_audio_data")

    audio_file = AudioFile(
        path=audio_path,
        data=b"fake_audio_data",
        size=100,
        extension=".mp3",
        filename="long_audio.mp3",
    )

    # Mock AudioSegment to avoid real audio processing
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 660000  # 11 minutes
        mock_segment.__getitem__.return_value = mock_segment

        def mock_export(buffer: BytesIO, format: str) -> None:
            buffer.write(b"fake_chunk_data")

        mock_segment.export = mock_export
        mock_audio_class.from_file.return_value = mock_segment

        chunks = chunk_audio_file(audio_file, chunk_duration_ms=300000)

        assert len(chunks) == 3
        assert all(isinstance(chunk, AudioFileChunk) for chunk in chunks)
        assert all(chunk.total_chunks == 3 for chunk in chunks)


def test_chunk_audio_file_single_chunk(tmp_path: Path) -> None:
    """Test short audio results in single chunk."""
    audio_path = tmp_path / "short_audio.mp3"
    audio_path.write_bytes(b"fake_audio_data")

    audio_file = AudioFile(
        path=audio_path,
        data=b"fake_audio_data",
        size=100,
        extension=".mp3",
        filename="short_audio.mp3",
    )

    # Mock AudioSegment
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 120000  # 2 minutes
        mock_segment.__getitem__.return_value = mock_segment

        def mock_export(buffer: BytesIO, format: str) -> None:
            buffer.write(b"fake_chunk_data")

        mock_segment.export = mock_export
        mock_audio_class.from_file.return_value = mock_segment

        chunks = chunk_audio_file(audio_file)

        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1


def test_chunk_audio_file_metadata_correct(tmp_path: Path) -> None:
    """Test chunk metadata accuracy."""
    audio_path = tmp_path / "test_audio.mp3"
    audio_path.write_bytes(b"fake_audio_data")

    audio_file = AudioFile(
        path=audio_path,
        data=b"fake_audio_data",
        size=100,
        extension=".mp3",
        filename="test_audio.mp3",
    )

    # Mock AudioSegment
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 420000  # 7 minutes
        mock_segment.__getitem__.return_value = mock_segment

        def mock_export(buffer: BytesIO, format: str) -> None:
            buffer.write(b"fake_chunk_data")

        mock_segment.export = mock_export
        mock_audio_class.from_file.return_value = mock_segment

        chunks = chunk_audio_file(audio_file, chunk_duration_ms=300000)

        assert len(chunks) == 2

        # Check chunk indices
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

        # Check total_chunks is same for all
        assert all(chunk.total_chunks == 2 for chunk in chunks)

        # Check start/end times are sequential
        assert chunks[0].start_time_ms == 0
        assert chunks[0].end_time_ms == 300000
        assert chunks[1].start_time_ms == 300000
        assert chunks[1].end_time_ms == 420000

        # Check original file references
        assert all(chunk.original_filename == "test_audio.mp3" for chunk in chunks)
        assert all(chunk.original_path == audio_path for chunk in chunks)


def test_chunk_audio_file_filenames(tmp_path: Path) -> None:
    """Test chunk filenames have index."""
    audio_path = tmp_path / "my_audio.mp3"
    audio_path.write_bytes(b"fake_audio_data")

    audio_file = AudioFile(
        path=audio_path,
        data=b"fake_audio_data",
        size=100,
        extension=".mp3",
        filename="my_audio.mp3",
    )

    # Mock AudioSegment
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 420000  # 7 minutes
        mock_segment.__getitem__.return_value = mock_segment

        def mock_export(buffer: BytesIO, format: str) -> None:
            buffer.write(b"fake_chunk_data")

        mock_segment.export = mock_export
        mock_audio_class.from_file.return_value = mock_segment

        chunks = chunk_audio_file(audio_file, chunk_duration_ms=300000)

        assert chunks[0].filename == "my_audio_chunk_0.mp3"
        assert chunks[1].filename == "my_audio_chunk_1.mp3"


def test_chunk_audio_file_custom_duration(tmp_path: Path) -> None:
    """Test custom chunk duration."""
    audio_path = tmp_path / "test.mp3"
    audio_path.write_bytes(b"fake_audio_data")

    audio_file = AudioFile(
        path=audio_path,
        data=b"fake_audio_data",
        size=100,
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock AudioSegment
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 150000  # 2.5 minutes
        mock_segment.__getitem__.return_value = mock_segment

        def mock_export(buffer: BytesIO, format: str) -> None:
            buffer.write(b"fake_chunk_data")

        mock_segment.export = mock_export
        mock_audio_class.from_file.return_value = mock_segment

        chunks = chunk_audio_file(audio_file, chunk_duration_ms=60000)

        assert len(chunks) == 3
        assert chunks[0].end_time_ms - chunks[0].start_time_ms == 60000
        assert chunks[1].end_time_ms - chunks[1].start_time_ms == 60000
        # Last chunk should be 30 seconds (remainder)
        assert chunks[2].end_time_ms - chunks[2].start_time_ms == 30000


def test_chunk_audio_file_valid_audio(tmp_path: Path) -> None:
    """Test chunks contain valid data."""
    audio_path = tmp_path / "test.mp3"
    audio_path.write_bytes(b"fake_audio_data")

    audio_file = AudioFile(
        path=audio_path,
        data=b"fake_audio_data",
        size=100,
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock AudioSegment
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 120000  # 2 minutes
        mock_segment.__getitem__.return_value = mock_segment

        def mock_export(buffer: BytesIO, format: str) -> None:
            buffer.write(b"fake_chunk_data")

        mock_segment.export = mock_export
        mock_audio_class.from_file.return_value = mock_segment

        chunks = chunk_audio_file(audio_file, chunk_duration_ms=60000)

        # Each chunk should have valid data
        for chunk in chunks:
            assert chunk.data == b"fake_chunk_data"
            assert len(chunk.data) > 0


def test_chunk_audio_file_openai_tuple(tmp_path: Path) -> None:
    """Test .file property returns correct tuple."""
    audio_path = tmp_path / "test.mp3"
    audio_path.write_bytes(b"fake_audio_data")

    audio_file = AudioFile(
        path=audio_path,
        data=b"fake_audio_data",
        size=100,
        extension=".mp3",
        filename="test.mp3",
    )

    # Mock AudioSegment
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 60000  # 1 minute
        mock_segment.__getitem__.return_value = mock_segment

        def mock_export(buffer: BytesIO, format: str) -> None:
            buffer.write(b"fake_chunk_data")

        mock_segment.export = mock_export
        mock_audio_class.from_file.return_value = mock_segment

        chunks = chunk_audio_file(audio_file)

        chunk = chunks[0]
        file_tuple = chunk.file
        assert isinstance(file_tuple, tuple)
        assert len(file_tuple) == 2
        assert file_tuple[0] == chunk.filename
        assert file_tuple[1] == chunk.data


def test_chunk_audio_file_invalid_audio(tmp_path: Path) -> None:
    """Test invalid audio raises AudioFileError."""
    # Create AudioFile with corrupted/invalid data
    audio_path = tmp_path / "invalid.mp3"
    invalid_data = b"This is not audio data"
    audio_path.write_bytes(invalid_data)

    audio_file = AudioFile(
        filename="invalid.mp3",
        data=invalid_data,
        path=audio_path,
        size=len(invalid_data),
        extension=".mp3",
    )

    # Mock AudioSegment to raise exception on invalid data
    with patch("infra.whisper.audio.AudioSegment") as mock_audio_class:
        mock_audio_class.from_file.side_effect = Exception("Invalid audio format")

        with pytest.raises(AudioFileError) as exc_info:
            chunk_audio_file(audio_file)

        assert "Failed to chunk audio file" in str(exc_info.value)
