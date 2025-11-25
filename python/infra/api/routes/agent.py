import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from python.infra.agent.client import summarize_transcript
from python.infra.api.dependencies import SettingsDepClean
from python.infra.whisper import open_audio_file_async, transcribe_audio
from python.infra.youtube import download_audio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/summary/{video_id}")
async def summarize_video(
    video_id: str, settings: SettingsDepClean
) -> StreamingResponse:
    """Stream progress updates for video summary generation via SSE.

    Raises YouTubeError, WhisperError, AgentError.
    """
    logger.info(f"Starting streaming video summary for: {video_id}")

    async def event_generator() -> AsyncIterator[str]:
        try:
            # Start processing
            msg = json.dumps({"status": "started", "message": "Starting summary generation..."})
            yield f"data: {msg}\n\n"
            await asyncio.sleep(0.1)

            # Download audio
            msg = json.dumps({
                "status": "downloading",
                "message": "Downloading audio from YouTube...",
            })
            yield f"data: {msg}\n\n"
            video_info = await download_audio(video_id, settings.downloads_dir)
            audio_path = video_info.downloaded_file

            # Transcribe
            msg = json.dumps({"status": "transcribing", "message": "Transcribing audio..."})
            yield f"data: {msg}\n\n"
            audio_file = await open_audio_file_async(audio_path)
            transcription = await transcribe_audio(audio_file)

            # Summarize
            msg = json.dumps({
                "status": "summarizing",
                "message": "Generating summary with Claude...",
            })
            yield f"data: {msg}\n\n"
            pdf_bytes = await summarize_transcript(transcription)

            # Complete with PDF data (base64 encoded)
            import base64

            pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
            msg = json.dumps({
                "status": "complete",
                "message": "Summary complete",
                "pdf": pdf_b64,
                "filename": f"{video_id}_summary.pdf",
            })
            yield f"data: {msg}\n\n"

            logger.info(f"Successfully streamed summary for: {video_id}")

        except Exception as e:
            error_msg = str(e) if str(e) else e.__class__.__name__
            error_type = f"{e.__class__.__module__}.{e.__class__.__name__}"

            # Clean one-line log on server
            logger.warning(
                f"Summary failed for {video_id}: {error_type}: {error_msg}"
            )

            # Send full error details to client
            msg = json.dumps({
                "status": "error",
                "message": error_msg,
                "error_type": e.__class__.__name__,
                "error_module": e.__class__.__module__,
            })
            yield f"data: {msg}\n\n"

    return StreamingResponse(
        event_generator(), media_type="text/event-stream"
    )
