"""Functional wrapper for transcript summarization using Claude API."""

import json
import logging
from contextlib import suppress
from datetime import datetime
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock
from jinja2 import Environment
from weasyprint import HTML  # type: ignore[import-untyped]

from python.infra.whisper import Transcription

from .dependencies import inject_deps
from .exceptions import PDFGenerationError, SummarizationError, TemplateRenderError
from .prompts import SUMMARY_PROMPT, SUMMARY_SYSTEM_PROMPT, SummaryResponse

logger = logging.getLogger(__name__)


def _extract_metadata(transcription: Transcription) -> dict[str, Any]:
    """Extract metadata from transcription for template rendering.

    Returns dict with title, channel, duration, date, video_id.
    """
    # Parse title and channel from filename if possible
    filename = str(transcription.audio_file)
    title = "Video Transcript Summary"
    channel = "Unknown Channel"
    video_id = None

    # Try to extract video ID from filename (common pattern: watch_v={id}.mp3)
    if "watch_v=" in filename:
        with suppress(IndexError, AttributeError):
            video_id = filename.split("watch_v=")[1].split(".")[0]

    # Format duration
    duration_seconds = int(transcription.duration or 0)
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60

    if hours > 0:
        duration_str = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        duration_str = f"{minutes}m {seconds}s"
    else:
        duration_str = f"{seconds}s"

    # Format date
    date_str = None
    if transcription.transcription_timestamp:
        date_str = transcription.transcription_timestamp.strftime("%Y-%m-%d")

    return {
        "title": title,
        "channel": channel,
        "duration": duration_str,
        "date": date_str,
        "video_id": video_id,
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


async def _call_claude_api(
    client: AsyncAnthropic,
    transcript_text: str,
) -> SummaryResponse:
    """Call Claude API to generate structured summary.

    Raises SummarizationError.
    """
    try:
        # Prepare the prompt
        prompt = SUMMARY_PROMPT.format(transcript=transcript_text)

        transcript_len = len(transcript_text)
        logger.info(
            f"Calling Claude API for summarization (transcript length: {transcript_len} chars)"
        )

        # Call Claude API
        message = await client.messages.create(
            model="claude-3-haiku-20240307",  # Fast and cost-effective for summaries
            max_tokens=4096,
            temperature=0.3,
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        logger.info("Claude API call completed successfully")

        # Extract text content
        if not message.content:
            raise SummarizationError("Claude returned empty response")

        # Find the first TextBlock
        response_text = None
        for block in message.content:
            if isinstance(block, TextBlock):
                response_text = block.text
                break

        if not response_text:
            raise SummarizationError("Claude returned no text content")

        # Parse JSON response
        try:
            response_data = json.loads(response_text)
            summary = SummaryResponse.model_validate(response_data)
        except (json.JSONDecodeError, ValueError) as e:
            raise SummarizationError(
                f"Failed to parse Claude response as JSON: {e}",
                {"response_preview": response_text[:200]},
            ) from e

        logger.info("Successfully generated summary from Claude")
        return summary

    except Exception as e:
        if isinstance(e, SummarizationError):
            raise
        raise SummarizationError(
            f"Claude API call failed: {e}",
            {"error_type": type(e).__name__},
        ) from e


def _render_html(
    summary: SummaryResponse,
    metadata: dict[str, Any],
    jinja_env: Environment,
) -> str:
    """Render HTML from Jinja2 template.

    Raises TemplateRenderError.
    """
    try:
        logger.info("Rendering HTML template")

        # Load template
        template = jinja_env.get_template("summary_template.html.tpl")

        # Prepare template context
        context = {
            **metadata,
            "headline": summary.headline,
            "key_points": summary.key_points,
            "concepts": summary.concepts,
            "narrative": summary.narrative,
        }

        # Render template
        html = template.render(**context)

        logger.info("Successfully rendered HTML template")
        return html

    except Exception as e:
        raise TemplateRenderError(
            f"Template rendering failed: {e}",
            {"template": "summary_template.html.tpl"},
        ) from e


def _generate_pdf(html: str) -> bytes:
    """Convert HTML to PDF using WeasyPrint.

    Raises PDFGenerationError.
    """
    try:
        logger.info("Generating PDF from HTML")

        # Create PDF from HTML
        pdf_document = HTML(string=html)
        pdf_bytes: bytes = pdf_document.write_pdf()

        if not pdf_bytes:
            raise PDFGenerationError("WeasyPrint returned empty PDF")

        logger.info(f"Successfully generated PDF ({len(pdf_bytes)} bytes)")
        return pdf_bytes

    except Exception as e:
        if isinstance(e, PDFGenerationError):
            raise
        raise PDFGenerationError(
            f"PDF generation failed: {e}",
            {"error_type": type(e).__name__},
        ) from e


@inject_deps
async def summarize_transcript(
    transcription: Transcription,
    client: AsyncAnthropic | None = None,
    jinja_env: Environment | None = None,
) -> bytes:
    """Summarize video transcript and generate PDF report.

    Takes a Transcription object, calls Claude API to generate structured summary,
    renders HTML from template, converts to PDF, and returns PDF bytes.

    Raises AgentError subclasses.
    """
    # Ensure dependencies are injected
    assert client is not None, "AsyncAnthropic client must be provided or injected"
    assert jinja_env is not None, "Jinja2 environment must be provided or injected"

    logger.info(f"Starting transcript summarization for: {transcription.audio_file}")

    try:
        # Extract metadata from transcription
        metadata = _extract_metadata(transcription)

        # Call Claude API to generate summary
        summary = await _call_claude_api(client, transcription.text)

        # Render HTML from template
        html = _render_html(summary, metadata, jinja_env)

        # Generate PDF from HTML
        pdf_bytes = _generate_pdf(html)

        logger.info("Successfully completed transcript summarization")
        return pdf_bytes

    except (SummarizationError, TemplateRenderError, PDFGenerationError):
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise SummarizationError(
            f"Unexpected error during summarization: {e}",
            {"audio_file": str(transcription.audio_file)},
        ) from e
