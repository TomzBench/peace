"""Tests for agent client."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from anthropic import AsyncAnthropic
from jinja2 import Environment

from python.infra.whisper import Transcription

from ..client import (
    _call_claude_api,
    _extract_metadata,
    _generate_pdf,
    _render_html,
    summarize_transcript,
)
from ..dependencies import override_dependency
from ..exceptions import SummarizationError, TemplateRenderError
from ..prompts import Concept, SummaryResponse

# Test fixtures


@pytest.fixture
def mock_transcription() -> Transcription:
    """Create a mock transcription object."""
    return Transcription(
        object="transcription",
        text="This is a test transcript about machine learning and AI.",
        segments=[],
        language="en",
        duration=120.5,
        audio_file=Path("watch_v=test123.mp3"),
        model_name="whisper-1",
        transcription_timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def mock_summary_response() -> SummaryResponse:
    """Create a mock summary response."""
    return SummaryResponse(
        headline="Test headline about AI",
        key_points=["Point 1", "Point 2", "Point 3"],
        concepts=[
            Concept(term="Machine Learning", definition="A type of AI"),
            Concept(term="Neural Network", definition="A computational model"),
        ],
        narrative=[
            "First paragraph of narrative.",
            "Second paragraph of narrative.",
        ],
    )


@pytest.fixture
def mock_anthropic_client() -> AsyncMock:
    """Create a mock Anthropic client."""
    client = AsyncMock(spec=AsyncAnthropic)
    return client


@pytest.fixture
def mock_jinja_env() -> Mock:
    """Create a mock Jinja2 environment."""
    env = Mock(spec=Environment)
    template = Mock()
    template.render = Mock(return_value="<html><body>Test HTML</body></html>")
    env.get_template = Mock(return_value=template)
    return env


# Test metadata extraction


def test_extract_metadata_basic(mock_transcription: Transcription) -> None:
    """Test basic metadata extraction."""
    metadata = _extract_metadata(mock_transcription)

    assert metadata["title"] == "Video Transcript Summary"
    assert metadata["channel"] == "Unknown Channel"
    assert metadata["duration"] == "2m 0s"
    assert metadata["date"] == "2024-01-01"
    assert metadata["video_id"] == "test123"
    assert "generation_date" in metadata


def test_extract_metadata_no_video_id() -> None:
    """Test metadata extraction without video ID in filename."""
    transcription = Transcription(
        object="transcription",
        text="Test",
        segments=[],
        language="en",
        duration=3661,  # 1h 1m 1s
        audio_file=Path("regular_file.mp3"),
        model_name="whisper-1",
        transcription_timestamp=datetime.now(),  # Use actual datetime
    )

    metadata = _extract_metadata(transcription)

    assert metadata["video_id"] is None
    assert metadata["duration"] == "1h 1m 1s"
    assert metadata["date"] is not None  # We provided a timestamp


def test_extract_metadata_short_duration() -> None:
    """Test metadata extraction with very short duration."""
    transcription = Transcription(
        object="transcription",
        text="Test",
        segments=[],
        language="en",
        duration=45,
        audio_file=Path("test.mp3"),
        model_name="whisper-1",
        transcription_timestamp=datetime.now(),
    )

    metadata = _extract_metadata(transcription)
    assert metadata["duration"] == "45s"


# Test Claude API call


@pytest.mark.asyncio
async def test_call_claude_api_success(
    mock_anthropic_client: AsyncMock,
    mock_summary_response: SummaryResponse,
) -> None:
    """Test successful Claude API call."""
    # Setup mock response - need to mock the TextBlock properly
    from anthropic.types import TextBlock

    mock_message = MagicMock()
    # Create a proper TextBlock instance
    text_block = TextBlock(type="text", text=json.dumps(mock_summary_response.model_dump()))
    mock_message.content = [text_block]

    # Create an async mock that returns the message
    async def mock_create(*args, **kwargs):  # type: ignore
        return mock_message

    mock_anthropic_client.messages.create = mock_create

    # Call function
    result = await _call_claude_api(mock_anthropic_client, "Test transcript")

    # Assertions
    assert isinstance(result, SummaryResponse)
    assert result.headline == mock_summary_response.headline
    assert result.key_points == mock_summary_response.key_points
    assert len(result.concepts) == 2
    # Can't use assert_called_once with async function, but we know it was called


@pytest.mark.asyncio
async def test_call_claude_api_empty_response(mock_anthropic_client: AsyncMock) -> None:
    """Test Claude API call with empty response."""
    # Setup mock with empty response
    mock_message = MagicMock()
    mock_message.content = []

    async def mock_create(*args, **kwargs):  # type: ignore
        return mock_message

    mock_anthropic_client.messages.create = mock_create

    # Call should raise error
    with pytest.raises(SummarizationError) as exc_info:
        await _call_claude_api(mock_anthropic_client, "Test transcript")

    assert "empty response" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_call_claude_api_invalid_json(mock_anthropic_client: AsyncMock) -> None:
    """Test Claude API call with invalid JSON response."""
    from anthropic.types import TextBlock

    # Setup mock with invalid JSON
    mock_message = MagicMock()
    text_block = TextBlock(type="text", text="This is not valid JSON")
    mock_message.content = [text_block]

    async def mock_create(*args, **kwargs):  # type: ignore
        return mock_message

    mock_anthropic_client.messages.create = mock_create

    # Call should raise error
    with pytest.raises(SummarizationError) as exc_info:
        await _call_claude_api(mock_anthropic_client, "Test transcript")

    assert "parse" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_call_claude_api_network_error(mock_anthropic_client: AsyncMock) -> None:
    """Test Claude API call with network error."""
    # Setup mock to raise exception
    async def mock_create_error(*args, **kwargs):  # type: ignore
        raise Exception("Network error")

    mock_anthropic_client.messages.create = mock_create_error

    # Call should wrap error
    with pytest.raises(SummarizationError) as exc_info:
        await _call_claude_api(mock_anthropic_client, "Test transcript")

    assert "Claude API call failed" in str(exc_info.value)


# Test HTML rendering


def test_render_html_success(
    mock_summary_response: SummaryResponse,
    mock_jinja_env: Mock,
) -> None:
    """Test successful HTML rendering."""
    metadata = {
        "title": "Test Title",
        "channel": "Test Channel",
        "duration": "10m",
        "date": "2024-01-01",
        "video_id": "test123",
        "generation_date": "2024-01-01 12:00",
    }

    html = _render_html(mock_summary_response, metadata, mock_jinja_env)

    assert html == "<html><body>Test HTML</body></html>"
    mock_jinja_env.get_template.assert_called_once_with("summary_template.html.tpl")


def test_render_html_template_error(
    mock_summary_response: SummaryResponse,
    mock_jinja_env: Mock,
) -> None:
    """Test HTML rendering with template error."""
    mock_jinja_env.get_template.side_effect = Exception("Template not found")
    metadata = {"title": "Test"}

    with pytest.raises(TemplateRenderError) as exc_info:
        _render_html(mock_summary_response, metadata, mock_jinja_env)

    assert "Template rendering failed" in str(exc_info.value)


# Test PDF generation


def test_generate_pdf_success() -> None:
    """Test successful PDF generation (basic check only)."""
    # This test just verifies the function returns PDF bytes
    # We can't fully mock WeasyPrint since it's a C extension
    html = "<html><body>Test</body></html>"
    pdf_bytes = _generate_pdf(html)

    # Basic check that we got PDF bytes
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")  # PDF files start with this


def test_generate_pdf_error_handling() -> None:
    """Test PDF generation with invalid HTML."""
    # WeasyPrint should still generate something even with minimal HTML
    html = "not really html"
    pdf_bytes = _generate_pdf(html)

    # Should still generate a PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


# Test main function with dependency injection


@pytest.mark.asyncio
async def test_summarize_transcript_success(
    mock_transcription: Transcription,
    mock_summary_response: SummaryResponse,
    mock_anthropic_client: AsyncMock,
    mock_jinja_env: Mock,
) -> None:
    """Test successful transcript summarization."""
    from anthropic.types import TextBlock

    # Setup mocks
    mock_message = MagicMock()
    text_block = TextBlock(type="text", text=json.dumps(mock_summary_response.model_dump()))
    mock_message.content = [text_block]

    async def mock_create(*args, **kwargs):  # type: ignore
        return mock_message

    mock_anthropic_client.messages.create = mock_create

    # Setup HTML template mock
    template = Mock()
    template.render = Mock(return_value="<html><body>Test</body></html>")
    mock_jinja_env.get_template.return_value = template

    # Call function with injected dependencies
    # Note: We can't mock WeasyPrint's HTML class since it's a C extension
    pdf_bytes = await summarize_transcript(
        mock_transcription,
        client=mock_anthropic_client,
        jinja_env=mock_jinja_env,
    )

    # Assertions - just check we got a valid PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
    # Can't use assert_called_once with async function
    mock_jinja_env.get_template.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_transcript_with_dependency_override(
    mock_transcription: Transcription,
    mock_summary_response: SummaryResponse,
) -> None:
    """Test transcript summarization with dependency override."""
    from anthropic.types import TextBlock

    # Create mock client
    mock_client = AsyncMock(spec=AsyncAnthropic)
    mock_message = MagicMock()
    text_block = TextBlock(type="text", text=json.dumps(mock_summary_response.model_dump()))
    mock_message.content = [text_block]

    async def mock_create(*args, **kwargs):  # type: ignore
        return mock_message

    mock_client.messages.create = mock_create

    # Create mock Jinja environment
    mock_env = Mock(spec=Environment)
    template = Mock()
    template.render = Mock(return_value="<html>Override Test</html>")
    mock_env.get_template.return_value = template

    # Use dependency override
    with override_dependency("client", lambda: mock_client), override_dependency(
        "jinja_env", lambda: mock_env
    ):
        pdf_bytes = await summarize_transcript(mock_transcription)

    # Check we got a valid PDF
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_summarize_transcript_api_error(
    mock_transcription: Transcription,
    mock_anthropic_client: AsyncMock,
    mock_jinja_env: Mock,
) -> None:
    """Test transcript summarization with API error."""
    # Setup mock to raise error
    async def mock_create_error(*args, **kwargs):  # type: ignore
        raise Exception("API error")

    mock_anthropic_client.messages.create = mock_create_error

    with pytest.raises(SummarizationError) as exc_info:
        await summarize_transcript(
            mock_transcription,
            client=mock_anthropic_client,
            jinja_env=mock_jinja_env,
        )

    assert "Claude API call failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_summarize_transcript_template_error(
    mock_transcription: Transcription,
    mock_summary_response: SummaryResponse,
    mock_anthropic_client: AsyncMock,
    mock_jinja_env: Mock,
) -> None:
    """Test transcript summarization with template error."""
    from anthropic.types import TextBlock

    # Setup Claude mock
    mock_message = MagicMock()
    text_block = TextBlock(type="text", text=json.dumps(mock_summary_response.model_dump()))
    mock_message.content = [text_block]

    async def mock_create(*args, **kwargs):  # type: ignore
        return mock_message

    mock_anthropic_client.messages.create = mock_create

    # Setup template error
    mock_jinja_env.get_template.side_effect = Exception("Template error")

    with pytest.raises(TemplateRenderError) as exc_info:
        await summarize_transcript(
            mock_transcription,
            client=mock_anthropic_client,
            jinja_env=mock_jinja_env,
        )

    assert "Template rendering failed" in str(exc_info.value)
