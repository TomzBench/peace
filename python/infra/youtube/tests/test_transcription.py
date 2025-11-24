"""Tests for YouTube transcription/subtitle extraction.

This module tests the get_transcriptions function.
"""

import pytest

from python.infra.youtube.client import get_transcriptions
from python.infra.youtube.exceptions import TranscriptionError
from python.infra.youtube.tests.helpers import (
    MockYoutubeDL,
    assert_transcriptions,
    make_mock_video_info_dict,
)


class TestGetTranscriptions:
    """Tests for get_transcriptions function."""

    @pytest.mark.asyncio
    async def test_get_transcriptions_success(self) -> None:
        """Test successful transcription extraction."""
        mock_data = make_mock_video_info_dict(
            video_id="jNQXAC9IVRw",
            title="Me at the zoo",
            include_subtitles=True,
        )

        # Add realistic subtitle data
        mock_data["subtitles"]["en"][0]["content"] = (
            "All right, so here we are in front of the elephants. "
            "The cool thing about these guys is that they have really, "
            "really, really long trunks."
        )

        with MockYoutubeDL(extract_info_return=mock_data):
            url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
            transcriptions = await get_transcriptions(url)

            # Use assertion helper
            assert_transcriptions(
                transcriptions,
                expected_count=2,  # en and es from mock
                expected_languages=["en", "es"],
                has_manual=True,
                has_auto=False,
            )

            # Check content
            en_transcript = next(t for t in transcriptions if t.language == "en")
            assert "elephant" in en_transcript.text.lower()
            assert "trunk" in en_transcript.text.lower()
            assert not en_transcript.auto_generated

    @pytest.mark.asyncio
    async def test_get_transcriptions_with_auto_captions(self) -> None:
        """Test extraction of auto-generated captions."""
        mock_data = make_mock_video_info_dict(
            include_subtitles=False,
            include_auto_captions=True,
        )

        with MockYoutubeDL(extract_info_return=mock_data):
            transcriptions = await get_transcriptions(
                "https://www.youtube.com/watch?v=test"
            )

            assert_transcriptions(
                transcriptions,
                expected_count=1,
                expected_languages=["en"],
                has_manual=False,
                has_auto=True,
            )

            auto_transcript = transcriptions[0]
            assert auto_transcript.auto_generated is True
            assert "[Auto-generated]" in auto_transcript.text

    @pytest.mark.asyncio
    async def test_get_transcriptions_mixed_sources(self) -> None:
        """Test extraction with both manual and auto-generated subtitles."""
        mock_data = make_mock_video_info_dict(
            include_subtitles=True,
            include_auto_captions=True,
        )

        with MockYoutubeDL(extract_info_return=mock_data):
            transcriptions = await get_transcriptions(
                "https://www.youtube.com/watch?v=test"
            )

            # Should have both manual and auto
            assert_transcriptions(
                transcriptions,
                has_manual=True,
                has_auto=True,
            )

            # Separate by type
            manual = [t for t in transcriptions if not t.auto_generated]
            auto = [t for t in transcriptions if t.auto_generated]

            assert len(manual) > 0
            assert len(auto) > 0

    @pytest.mark.asyncio
    async def test_get_transcriptions_with_language_filter(self) -> None:
        """Test transcription extraction with language filter."""
        mock_data = {
            **make_mock_video_info_dict(),
            "subtitles": {
                "en": [
                    {
                        "ext": "vtt",
                        "url": "https://example.com/en.vtt",
                        "content": "English subtitle text",
                    }
                ],
                "es": [
                    {
                        "ext": "vtt",
                        "url": "https://example.com/es.vtt",
                        "content": "Spanish subtitle text",
                    }
                ],
                "fr": [
                    {
                        "ext": "vtt",
                        "url": "https://example.com/fr.vtt",
                        "content": "French subtitle text",
                    }
                ],
            },
            "automatic_captions": {},
        }

        with MockYoutubeDL(extract_info_return=mock_data):
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            transcriptions = await get_transcriptions(url, languages=["en", "fr"])

            # Should only get en and fr
            assert_transcriptions(
                transcriptions,
                expected_count=2,
                expected_languages=["en", "fr"],
            )

            # Verify es was filtered out
            languages = {t.language for t in transcriptions}
            assert "es" not in languages

    @pytest.mark.asyncio
    async def test_get_transcriptions_empty_filter(self) -> None:
        """Test with empty language filter (should return all)."""
        mock_data = make_mock_video_info_dict(include_subtitles=True)

        with MockYoutubeDL(extract_info_return=mock_data):
            transcriptions = await get_transcriptions(
                "https://www.youtube.com/watch?v=test",
                languages=[],
            )

            # Empty filter should return all available
            assert len(transcriptions) > 0

    @pytest.mark.asyncio
    async def test_get_transcriptions_no_subtitles(self) -> None:
        """Test video with no subtitles or captions."""
        mock_data = {
            **make_mock_video_info_dict(),
            "subtitles": {},
            "automatic_captions": {},
        }

        with MockYoutubeDL(extract_info_return=mock_data):
            transcriptions = await get_transcriptions(
                "https://www.youtube.com/watch?v=nosubs"
            )

            assert transcriptions == []

    @pytest.mark.asyncio
    async def test_get_transcriptions_invalid_language_code(self) -> None:
        """Test filtering with invalid language codes."""
        mock_data = make_mock_video_info_dict(include_subtitles=True)

        with MockYoutubeDL(extract_info_return=mock_data):
            # Invalid codes should just return no matches
            transcriptions = await get_transcriptions(
                "https://www.youtube.com/watch?v=test",
                languages=["xyz", "abc"],  # Invalid codes
            )

            assert transcriptions == []

    @pytest.mark.asyncio
    async def test_get_transcriptions_multiple_formats(self) -> None:
        """Test handling multiple subtitle formats for same language."""
        mock_data = {
            **make_mock_video_info_dict(),
            "subtitles": {
                "en": [
                    {
                        "ext": "vtt",
                        "url": "https://example.com/en.vtt",
                        "content": "VTT format content",
                    },
                    {
                        "ext": "srv3",
                        "url": "https://example.com/en.srv3",
                        "content": "SRV3 format content",
                    },
                    {
                        "ext": "json3",
                        "url": "https://example.com/en.json3",
                        "content": "JSON3 format content",
                    },
                ],
            },
            "automatic_captions": {},
        }

        with MockYoutubeDL(extract_info_return=mock_data):
            transcriptions = await get_transcriptions(
                "https://www.youtube.com/watch?v=test"
            )

            # Should handle multiple formats gracefully
            en_transcripts = [t for t in transcriptions if t.language == "en"]
            assert len(en_transcripts) > 0

            # Should have content from one of the formats
            en_transcript = en_transcripts[0]
            assert en_transcript.text in [
                "VTT format content",
                "SRV3 format content",
                "JSON3 format content",
            ]


class TestGetTranscriptionsErrors:
    """Test error handling in get_transcriptions."""

    @pytest.mark.asyncio
    async def test_get_transcriptions_error(self) -> None:
        """Test transcription extraction error handling."""
        error = Exception("Unexpected error")

        with MockYoutubeDL(extract_info_side_effect=error), pytest.raises(
            TranscriptionError, match="Unexpected error"
        ):
            await get_transcriptions("https://www.youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_get_transcriptions_missing_data(self) -> None:
        """Test handling of missing subtitle data in response."""
        mock_data = make_mock_video_info_dict()
        # Remove subtitle fields
        mock_data.pop("subtitles", None)
        mock_data.pop("automatic_captions", None)

        with MockYoutubeDL(extract_info_return=mock_data):
            # Should handle gracefully and return empty list
            transcriptions = await get_transcriptions(
                "https://www.youtube.com/watch?v=test"
            )
            assert transcriptions == []
