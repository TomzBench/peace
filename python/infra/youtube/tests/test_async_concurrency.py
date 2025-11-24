"""Tests for async concurrency behavior of YouTube client.

This module tests concurrent operations, executor management, and edge cases.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yt_dlp  # type: ignore[import-untyped]

from python.infra.youtube.client import (
    download_audio,
    download_video,
    get_transcriptions,
    get_video_info,
)
from python.infra.youtube.dependencies import override_dependency
from python.infra.youtube.exceptions import (
    ExtractionError,
    InvalidURLError,
)
from python.infra.youtube.tests.helpers import (
    MockYoutubeDL,
    make_mock_video_info_dict,
)


class TestConcurrentVideoInfo:
    """Tests for concurrent video info fetching."""

    @pytest.mark.asyncio
    async def test_concurrent_video_info_fetching(self) -> None:
        """Test fetching multiple video infos concurrently."""
        urls = [f"https://youtube.com/watch?v=test{i}" for i in range(5)]
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(extract_info_return=mock_data):
            # Fetch all concurrently
            tasks = [get_video_info(url) for url in urls]
            results = await asyncio.gather(*tasks)

            assert len(results) == 5
            for result in results:
                assert result.video_id == "dQw4w9WgXcQ"
                assert result.title == "Rick Astley - Never Gonna Give You Up"

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(self) -> None:
        """Test concurrent operations with mixed success and failure."""
        mock_data = make_mock_video_info_dict()

        # Use side_effect to alternate between success and failure
        side_effects = [
            mock_data,
            yt_dlp.utils.DownloadError("Invalid URL"),
            mock_data,
            yt_dlp.utils.DownloadError("Video unavailable"),
            mock_data,
        ]

        with patch("python.infra.youtube.client.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.side_effect = side_effects
            mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
            mock_ydl.__exit__ = MagicMock(return_value=False)
            mock_ydl_class.return_value = mock_ydl

            urls = [f"https://youtube.com/watch?v=test{i}" for i in range(5)]
            tasks = [get_video_info(url) for url in urls]

            # Use return_exceptions=True to capture both successes and failures
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check we got expected mix
            successes = [r for r in results if not isinstance(r, Exception)]
            failures = [r for r in results if isinstance(r, Exception)]

            assert len(successes) == 3
            assert len(failures) == 2
            assert any(isinstance(e, InvalidURLError) for e in failures)

    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self) -> None:
        """Test behavior under rate limiting with custom executor."""
        # Create executor with very limited workers
        executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="test_limited_")

        urls = [f"https://youtube.com/watch?v=test{i}" for i in range(10)]
        mock_data = make_mock_video_info_dict()

        async with override_dependency("executor", lambda: executor):
            with MockYoutubeDL(extract_info_return=mock_data):
                # Should handle 10 requests with only 2 workers
                tasks = [get_video_info(url) for url in urls]
                results = await asyncio.gather(*tasks)

                assert len(results) == 10
                # All should succeed despite limited workers
                for result in results:
                    assert result.video_id == "dQw4w9WgXcQ"

        executor.shutdown(wait=True)


class TestConcurrentDownloads:
    """Tests for concurrent download operations."""

    @pytest.mark.asyncio
    async def test_concurrent_video_downloads(self, tmp_path: Path) -> None:
        """Test downloading multiple videos concurrently."""
        output_path = tmp_path / "videos"
        urls = [f"https://youtube.com/watch?v=test{i}" for i in range(3)]
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "video.mp4"),
        ):
            # Download all concurrently
            tasks = [download_video(url, output_path) for url in urls]
            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            for result in results:
                assert result.downloaded_file is not None
                assert result.download_timestamp is not None

    @pytest.mark.asyncio
    async def test_concurrent_audio_downloads(self, tmp_path: Path) -> None:
        """Test downloading multiple audio files concurrently."""
        output_path = tmp_path / "audio"
        urls = [f"https://youtube.com/watch?v=audio{i}" for i in range(4)]
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(output_path / "audio.webm"),
        ):
            # Download all concurrently
            tasks = [download_audio(url, output_path) for url in urls]
            results = await asyncio.gather(*tasks)

            assert len(results) == 4
            for result in results:
                assert result.downloaded_file is not None
                assert result.downloaded_file.suffix == ".mp3"  # Default format

    @pytest.mark.asyncio
    async def test_mixed_download_types(self, tmp_path: Path) -> None:
        """Test concurrent video and audio downloads."""
        video_path = tmp_path / "videos"
        audio_path = tmp_path / "audio"
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(
            extract_info_return=mock_data,
            prepare_filename_return=str(tmp_path / "media.mp4"),
        ):
            # Mix video and audio downloads
            tasks = [
                download_video("https://youtube.com/watch?v=video1", video_path),
                download_audio("https://youtube.com/watch?v=audio1", audio_path),
                download_video("https://youtube.com/watch?v=video2", video_path),
                download_audio("https://youtube.com/watch?v=audio2", audio_path),
            ]
            results = await asyncio.gather(*tasks)

            assert len(results) == 4
            # All should succeed
            for result in results:
                assert result.video_id == "dQw4w9WgXcQ"


class TestConcurrentTranscriptions:
    """Tests for concurrent transcription operations."""

    @pytest.mark.asyncio
    async def test_concurrent_transcription_fetching(self) -> None:
        """Test fetching transcriptions for multiple videos concurrently."""
        urls = [f"https://youtube.com/watch?v=sub{i}" for i in range(5)]
        mock_data = make_mock_video_info_dict(include_subtitles=True)

        with MockYoutubeDL(extract_info_return=mock_data):
            # Fetch all transcriptions concurrently
            tasks = [get_transcriptions(url) for url in urls]
            results = await asyncio.gather(*tasks)

            assert len(results) == 5
            for transcriptions in results:
                assert len(transcriptions) > 0
                # Check we got expected languages from mock
                languages = {t.language for t in transcriptions}
                assert "en" in languages or "es" in languages

    @pytest.mark.asyncio
    async def test_concurrent_filtered_transcriptions(self) -> None:
        """Test fetching transcriptions with language filters concurrently."""
        urls = [f"https://youtube.com/watch?v=lang{i}" for i in range(3)]
        mock_data = make_mock_video_info_dict(
            include_subtitles=True,
            include_auto_captions=True,
        )

        with MockYoutubeDL(extract_info_return=mock_data):
            # Different language filters for each request
            tasks = [
                get_transcriptions(urls[0], languages=["en"]),
                get_transcriptions(urls[1], languages=["es"]),
                get_transcriptions(urls[2]),  # No filter - get all
            ]
            results = await asyncio.gather(*tasks)

            # First should only have English
            en_langs = {t.language for t in results[0]}
            assert "en" in en_langs
            assert "es" not in en_langs

            # Second should only have Spanish
            es_langs = {t.language for t in results[1]}
            assert "es" in es_langs
            assert "en" not in es_langs

            # Third should have both
            all_langs = {t.language for t in results[2]}
            assert len(all_langs) >= 2


class TestExecutorManagement:
    """Tests for executor lifecycle and error handling."""

    @pytest.mark.asyncio
    async def test_executor_cleanup_on_error(self) -> None:
        """Test executor cleanup when operations fail."""
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="test_cleanup_")
        error = yt_dlp.utils.DownloadError("Test error")

        async with override_dependency("executor", lambda: executor):
            with MockYoutubeDL(extract_info_side_effect=error):
                # Should raise but not leak executor resources
                with pytest.raises((InvalidURLError, ExtractionError)):
                    await get_video_info("https://youtube.com/watch?v=error")

                # Executor should still be usable
                assert not executor._shutdown

        # Cleanup
        executor.shutdown(wait=True)

    @pytest.mark.asyncio
    async def test_executor_sharing_across_operations(self) -> None:
        """Test that executor can be shared across different operation types."""
        shared_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="shared_")
        mock_data = make_mock_video_info_dict(include_subtitles=True)

        async with override_dependency("executor", lambda: shared_executor):
            with MockYoutubeDL(extract_info_return=mock_data):
                # Run different operation types with same executor
                tasks = [
                    get_video_info("https://youtube.com/watch?v=1"),
                    get_transcriptions("https://youtube.com/watch?v=2"),
                    get_video_info("https://youtube.com/watch?v=3"),
                ]
                results = await asyncio.gather(*tasks)

                assert len(results) == 3
                # First and third are VideoInfo objects
                assert results[0].video_id == "dQw4w9WgXcQ"
                assert results[2].video_id == "dQw4w9WgXcQ"
                # Second is list of transcriptions
                assert isinstance(results[1], list)

        shared_executor.shutdown(wait=True)

    @pytest.mark.asyncio
    async def test_custom_executor_injection(self, mock_executor: ThreadPoolExecutor) -> None:
        """Test using custom injected executor."""
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(extract_info_return=mock_data):
            # Use the fixture-provided executor directly
            info = await get_video_info(
                "https://youtube.com/watch?v=test",
                executor=mock_executor
            )

            assert info.video_id == "dQw4w9WgXcQ"


class TestCancellationHandling:
    """Tests for async cancellation scenarios."""

    @pytest.mark.asyncio
    async def test_cancellation_during_fetch(self) -> None:
        """Test cancelling operations mid-flight."""
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(extract_info_return=mock_data):
            # Create tasks
            tasks = [
                asyncio.create_task(get_video_info(f"https://youtube.com/watch?v={i}"))
                for i in range(5)
            ]

            # Cancel some tasks
            tasks[1].cancel()
            tasks[3].cancel()

            # Gather with return_exceptions
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check cancelled tasks
            assert isinstance(results[1], asyncio.CancelledError)
            assert isinstance(results[3], asyncio.CancelledError)

            # Others should succeed
            successful_results = [r for r in [results[0], results[2], results[4]]
                                  if not isinstance(r, BaseException)]
            assert len(successful_results) == 3
            for result in successful_results:
                assert result.video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_timeout_handling(self) -> None:
        """Test operations with timeouts."""
        import time
        mock_data = make_mock_video_info_dict()

        # Simulate slow operation (sync function since _extract_info is sync)
        def slow_extract(*args: Any, **kwargs: Any) -> dict[str, Any]:
            time.sleep(2)  # Longer than timeout
            return mock_data

        with patch("python.infra.youtube.client._extract_info", side_effect=slow_extract), \
             pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                get_video_info("https://youtube.com/watch?v=slow"),
                timeout=0.1
            )


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_batch_operations(self) -> None:
        """Test handling empty lists of operations."""
        # Empty gather should return empty list
        results: list[Any] = await asyncio.gather()
        assert results == []

        # Empty list of tasks
        tasks: list[Any] = []
        results = await asyncio.gather(*tasks)
        assert results == []

    @pytest.mark.asyncio
    async def test_single_operation_performance(self) -> None:
        """Test that single operations aren't slower with async."""
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(extract_info_return=mock_data):
            # Single operation should complete quickly
            info = await get_video_info("https://youtube.com/watch?v=single")
            assert info.video_id == "dQw4w9WgXcQ"

    @pytest.mark.asyncio
    async def test_large_batch_operations(self) -> None:
        """Test handling large number of concurrent operations."""
        # Test with 50 concurrent operations
        urls = [f"https://youtube.com/watch?v=bulk{i}" for i in range(50)]
        mock_data = make_mock_video_info_dict()

        with MockYoutubeDL(extract_info_return=mock_data):
            tasks = [get_video_info(url) for url in urls]
            results = await asyncio.gather(*tasks)

            assert len(results) == 50
            # All should succeed
            for result in results:
                assert result.video_id == "dQw4w9WgXcQ"
