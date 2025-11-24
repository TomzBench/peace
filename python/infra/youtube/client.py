"""Functional wrapper for yt-dlp YouTube downloads."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import yt_dlp  # type: ignore[import-untyped]

from python.infra.youtube.exceptions import (
    DownloadError,
    ExtractionError,
    InvalidURLError,
    TranscriptionError,
    UnavailableVideoError,
)
from python.infra.youtube.models import (
    AudioDownloadOptions,
    Format,
    Thumbnail,
    Transcription,
    VideoDownloadOptions,
    VideoInfo,
)

from .dependencies import inject_deps

logger = logging.getLogger(__name__)

# Base yt-dlp options used across all operations
_BASE_YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
}


def _classify_ytdlp_download_error(e: yt_dlp.utils.DownloadError, url: str) -> Exception:
    """Classify yt-dlp DownloadError into appropriate exception type."""
    error_msg = str(e).lower()
    if "unavailable" in error_msg or "private" in error_msg:
        return UnavailableVideoError(str(e), url)
    if "invalid" in error_msg or "url" in error_msg:
        return InvalidURLError(str(e), url)
    return DownloadError(str(e), url)


def _prepare_output_directory(output_path: Path) -> Path:
    """Prepare output directory for downloads."""
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _extract_info(url: str, extract_flat: bool = False) -> dict[str, Any]:
    """Extract video information using yt-dlp.

    Raises InvalidURLError, UnavailableVideoError, ExtractionError.
    """
    ydl_opts = {
        **_BASE_YDL_OPTS,
        "extract_flat": extract_flat,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise ExtractionError("Failed to extract video information", url)
            return info  # type: ignore[no-any-return]
    except yt_dlp.utils.DownloadError as e:
        exc = _classify_ytdlp_download_error(e, url)
        # Convert DownloadError to ExtractionError for extract_info context
        if isinstance(exc, DownloadError) and not isinstance(
            exc, (InvalidURLError, UnavailableVideoError)
        ):
            raise ExtractionError(str(e), url) from e
        raise exc from e
    except Exception as e:
        raise ExtractionError(f"Unexpected error: {e}", url) from e


@inject_deps
async def get_video_info(url: str, *, executor: ThreadPoolExecutor | None = None) -> VideoInfo:
    """Extract video metadata without downloading.

    Raises InvalidURLError, UnavailableVideoError, ExtractionError.
    """
    assert executor is not None, "Executor must be provided or injected"
    logger.info(f"Extracting video info for: {url}")

    loop = asyncio.get_event_loop()
    # Run blocking _extract_info in executor
    info = await loop.run_in_executor(executor, _extract_info, url)

    video_info = _build_video_info(info, url)

    logger.info(f"Successfully extracted info for: {video_info.title}")
    return video_info


def _build_video_info(
    info: dict[str, Any],
    url: str,
    downloaded_file: Path | None = None,
    download_timestamp: datetime | None = None,
) -> VideoInfo:
    """Build VideoInfo from yt-dlp info dict."""
    formats = [Format.model_validate(f) for f in info.get("formats", [])]
    thumbnails = [Thumbnail.model_validate(t) for t in info.get("thumbnails", [])]

    video_info_dict = {
        **info,
        "url": url,
        "formats": formats,
        "thumbnails": thumbnails,
    }

    if downloaded_file is not None:
        video_info_dict["downloaded_file"] = downloaded_file

    if download_timestamp is not None:
        video_info_dict["download_timestamp"] = download_timestamp

    return VideoInfo.model_validate(video_info_dict)


def _download_sync(url: str, ydl_opts: dict[str, Any]) -> dict[str, Any]:
    """Synchronous download logic for both video and audio.

    Raises DownloadError.
    """
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise DownloadError("Download returned no information", url)
        # Store the prepared filename for later use
        info["_prepared_filename"] = ydl.prepare_filename(info)
        return info  # type: ignore[no-any-return]


@inject_deps
async def download_video(
    url: str,
    output_path: Path,
    options: VideoDownloadOptions | None = None,
    *,
    executor: ThreadPoolExecutor | None = None,
) -> VideoInfo:
    """Download video and return metadata.

    Raises InvalidURLError, UnavailableVideoError, DownloadError.
    """
    assert executor is not None, "Executor must be provided or injected"
    options = options or VideoDownloadOptions()
    logger.info(f"Downloading video: {url}")

    output_path = _prepare_output_directory(output_path)

    ydl_opts = {
        **_BASE_YDL_OPTS,
        "format": options.format,
        "outtmpl": str(output_path / "%(title)s.%(ext)s"),
        **options.ydl_opts,
    }

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(executor, _download_sync, url, ydl_opts)

        # Get the actual downloaded file path
        downloaded_file = Path(info["_prepared_filename"])

        video_info = _build_video_info(
            info, url, downloaded_file=downloaded_file, download_timestamp=datetime.now()
        )

        logger.info(f"Successfully downloaded: {video_info.title}")
        return video_info

    except yt_dlp.utils.DownloadError as e:
        raise _classify_ytdlp_download_error(e, url) from e
    except Exception as e:
        raise DownloadError(f"Unexpected error during download: {e}", url) from e


@inject_deps
async def download_audio(
    url: str,
    output_path: Path,
    options: AudioDownloadOptions | None = None,
    *,
    executor: ThreadPoolExecutor | None = None,
) -> VideoInfo:
    """Download audio only and return metadata.

    Raises InvalidURLError, UnavailableVideoError, DownloadError.
    """
    assert executor is not None, "Executor must be provided or injected"
    options = options or AudioDownloadOptions()
    logger.info(f"Downloading audio: {url}")

    output_path = _prepare_output_directory(output_path)

    ydl_opts = {
        **_BASE_YDL_OPTS,
        "format": "bestaudio/best",
        "outtmpl": str(output_path / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": options.format,
                "preferredquality": options.quality,
            }
        ],
        **options.ydl_opts,
    }

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(executor, _download_sync, url, ydl_opts)

        # Determine the final filename (after postprocessing)
        base_filename = info["_prepared_filename"]
        downloaded_file = Path(base_filename).with_suffix(f".{options.format}")

        video_info = _build_video_info(
            info, url, downloaded_file=downloaded_file, download_timestamp=datetime.now()
        )

        logger.info(f"Successfully downloaded audio: {video_info.title}")
        return video_info

    except yt_dlp.utils.DownloadError as e:
        raise _classify_ytdlp_download_error(e, url) from e
    except Exception as e:
        raise DownloadError(f"Unexpected error during audio download: {e}", url) from e


def _extract_subtitle_for_language(
    lang: str,
    sub_list: Any,
    auto_generated: bool,
    language_filter: list[str] | None,
) -> Transcription | None:
    """Extract first valid subtitle for a language."""
    # Apply language filter
    if language_filter and lang not in language_filter:
        return None

    # Skip if sub_list is malformed (not a list)
    if not isinstance(sub_list, list):
        return None

    # Get the first subtitle format with content
    for sub in sub_list:
        if not isinstance(sub, dict):
            continue
        text = sub.get("content", "")
        if text:  # Only include if we have actual content
            return Transcription(
                language=lang,
                text=text,
                auto_generated=auto_generated,
                ext=sub.get("ext", "vtt"),
            )

    return None


@inject_deps
async def get_transcriptions(
    url: str, languages: list[str] | None = None, *, executor: ThreadPoolExecutor | None = None
) -> list[Transcription]:
    """Extract available subtitles/transcriptions for a video.

    Raises InvalidURLError, UnavailableVideoError, TranscriptionError.
    """
    assert executor is not None, "Executor must be provided or injected"
    logger.info(f"Extracting transcriptions for: {url}")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(executor, _extract_info, url)
        transcriptions = []

        # Extract manual subtitles
        for lang, sub_list in info.get("subtitles", {}).items():
            if transcription := _extract_subtitle_for_language(lang, sub_list, False, languages):
                transcriptions.append(transcription)

        # Extract auto-generated subtitles
        for lang, sub_list in info.get("automatic_captions", {}).items():
            if transcription := _extract_subtitle_for_language(lang, sub_list, True, languages):
                transcriptions.append(transcription)

        logger.info(f"Found {len(transcriptions)} transcriptions")
        return transcriptions

    except (InvalidURLError, UnavailableVideoError):
        raise
    except ExtractionError as e:
        raise TranscriptionError(e.message, url) from e
    except Exception as e:
        raise TranscriptionError(f"Failed to extract transcriptions: {e}", url) from e
