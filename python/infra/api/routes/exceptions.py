"""FastAPI exception handlers for domain exceptions."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from python.infra.whisper.exceptions import WhisperError
from python.infra.youtube.exceptions import (
    DownloadError,
    ExtractionError,
    InvalidURLError,
    TranscriptionError,
    UnavailableVideoError,
    YouTubeError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""

    @app.exception_handler(YouTubeError)
    async def youtube_exception_handler(request: Request, exc: YouTubeError) -> JSONResponse:
        """Handle YouTube module exceptions.

        Raises YouTubeError and subclasses.
        """
        status_code = 400
        if isinstance(exc, UnavailableVideoError):
            status_code = 404
        elif isinstance(exc, InvalidURLError):
            status_code = 400
        elif isinstance(exc, (ExtractionError, DownloadError, TranscriptionError)):
            status_code = 500

        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "url": getattr(exc, "url", None),
            },
        )

    @app.exception_handler(WhisperError)
    async def whisper_exception_handler(request: Request, exc: WhisperError) -> JSONResponse:
        """Handle Whisper module exceptions.

        Raises WhisperError and subclasses.
        """
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "file_path": getattr(exc, "file_path", None),
            },
        )
