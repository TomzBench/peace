"""Functional wrapper for yt-dlp YouTube downloads."""

import logging
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

logger = logging.getLogger(__name__)


def _extract_info(url: str, extract_flat: bool = False) -> dict[str, Any]:
    """Extract video information using yt-dlp.

    Args:
        url: YouTube video URL
        extract_flat: If True, only extract basic info (faster)

    Returns:
        Raw info dict from yt-dlp

    Raises:
        InvalidURLError: URL is invalid or unsupported
        UnavailableVideoError: Video is unavailable
        ExtractionError: Other extraction errors
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": extract_flat,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise ExtractionError("Failed to extract video information", url)
            return info  # type: ignore[no-any-return]
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if "unavailable" in error_msg or "private" in error_msg:
            raise UnavailableVideoError(str(e), url) from e
        if "invalid" in error_msg or "url" in error_msg:
            raise InvalidURLError(str(e), url) from e
        raise ExtractionError(str(e), url) from e
    except Exception as e:
        raise ExtractionError(f"Unexpected error: {e}", url) from e


def _parse_formats(formats_data: list[dict[str, Any]]) -> list[Format]:
    """Parse format data from yt-dlp into Format models.

    Args:
        formats_data: Raw format list from yt-dlp

    Returns:
        List of Format models
    """
    formats = []
    for fmt in formats_data:
        try:
            formats.append(
                Format(
                    format_id=fmt["format_id"],
                    ext=fmt.get("ext", "unknown"),
                    format_note=fmt.get("format_note"),
                    filesize=fmt.get("filesize"),
                    filesize_approx=fmt.get("filesize_approx"),
                    tbr=fmt.get("tbr"),
                    vcodec=fmt.get("vcodec"),
                    acodec=fmt.get("acodec"),
                    fps=fmt.get("fps"),
                    width=fmt.get("width"),
                    height=fmt.get("height"),
                    resolution=fmt.get("resolution"),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to parse format {fmt.get('format_id')}: {e}")
            continue
    return formats


def _parse_thumbnails(thumbnails_data: list[dict[str, Any]]) -> list[Thumbnail]:
    """Parse thumbnail data from yt-dlp into Thumbnail models.

    Args:
        thumbnails_data: Raw thumbnail list from yt-dlp

    Returns:
        List of Thumbnail models
    """
    thumbnails = []
    for thumb in thumbnails_data:
        try:
            thumbnails.append(
                Thumbnail(
                    url=thumb["url"],
                    width=thumb.get("width"),
                    height=thumb.get("height"),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to parse thumbnail: {e}")
            continue
    return thumbnails


def get_video_info(url: str) -> VideoInfo:
    """Extract video metadata without downloading.

    Args:
        url: YouTube video URL

    Returns:
        VideoInfo with complete metadata

    Raises:
        InvalidURLError: URL is invalid
        UnavailableVideoError: Video is unavailable
        ExtractionError: Failed to extract information

    Examples:
        >>> info = get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        >>> print(f"{info.title} by {info.uploader}")
    """
    logger.info(f"Extracting video info for: {url}")

    info = _extract_info(url)

    # Parse formats and thumbnails
    formats = _parse_formats(info.get("formats", []))
    thumbnails = _parse_thumbnails(info.get("thumbnails", []))

    video_info = VideoInfo(
        url=url,  # type: ignore[arg-type]
        video_id=info["id"],
        title=info["title"],
        description=info.get("description"),
        uploader=info.get("uploader"),
        uploader_id=info.get("uploader_id"),
        channel=info.get("channel"),
        channel_id=info.get("channel_id"),
        upload_date=info.get("upload_date"),
        timestamp=info.get("timestamp"),
        duration=info.get("duration"),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        comment_count=info.get("comment_count"),
        age_limit=info.get("age_limit", 0),
        is_live=info.get("is_live", False),
        was_live=info.get("was_live", False),
        formats=formats,
        thumbnails=thumbnails,
        categories=info.get("categories", []),
        tags=info.get("tags", []),
    )

    logger.info(f"Successfully extracted info for: {video_info.title}")
    return video_info


def download_video(
    url: str,
    output_path: Path,
    options: VideoDownloadOptions | None = None,
) -> VideoInfo:
    """Download video and return metadata.

    Args:
        url: YouTube video URL
        output_path: Directory to save video
        options: Download options (format, additional yt-dlp options)

    Returns:
        VideoInfo with download information

    Raises:
        InvalidURLError: URL is invalid
        UnavailableVideoError: Video is unavailable
        DownloadError: Download failed

    Examples:
        >>> opts = VideoDownloadOptions(
        ...     format="bestvideo[height<=720]+bestaudio/best[height<=720]"
        ... )
        >>> info = download_video("https://youtube.com/watch?v=...", Path("downloads"), opts)
    """
    options = options or VideoDownloadOptions()
    logger.info(f"Downloading video: {url}")

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": options.format,
        "outtmpl": str(output_path / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        **options.ydl_opts,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise DownloadError("Download returned no information", url)

            # Get the actual downloaded file path
            downloaded_file = Path(ydl.prepare_filename(info))

            # Parse formats and thumbnails
            formats = _parse_formats(info.get("formats", []))
            thumbnails = _parse_thumbnails(info.get("thumbnails", []))

            video_info = VideoInfo(
                url=url,  # type: ignore[arg-type]
                video_id=info["id"],
                title=info["title"],
                description=info.get("description"),
                uploader=info.get("uploader"),
                uploader_id=info.get("uploader_id"),
                channel=info.get("channel"),
                channel_id=info.get("channel_id"),
                upload_date=info.get("upload_date"),
                timestamp=info.get("timestamp"),
                duration=info.get("duration"),
                view_count=info.get("view_count"),
                like_count=info.get("like_count"),
                comment_count=info.get("comment_count"),
                age_limit=info.get("age_limit", 0),
                is_live=info.get("is_live", False),
                was_live=info.get("was_live", False),
                formats=formats,
                thumbnails=thumbnails,
                categories=info.get("categories", []),
                tags=info.get("tags", []),
                downloaded_file=downloaded_file,
                download_timestamp=datetime.now(),
            )

            logger.info(f"Successfully downloaded: {video_info.title}")
            return video_info

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if "unavailable" in error_msg or "private" in error_msg:
            raise UnavailableVideoError(str(e), url) from e
        if "invalid" in error_msg or "url" in error_msg:
            raise InvalidURLError(str(e), url) from e
        raise DownloadError(str(e), url) from e
    except Exception as e:
        raise DownloadError(f"Unexpected error during download: {e}", url) from e


def download_audio(
    url: str,
    output_path: Path,
    options: AudioDownloadOptions | None = None,
) -> VideoInfo:
    """Download audio only and return metadata.

    Args:
        url: YouTube video URL
        output_path: Directory to save audio
        options: Audio download options (format, quality, additional yt-dlp options)

    Returns:
        VideoInfo with download information

    Raises:
        InvalidURLError: URL is invalid
        UnavailableVideoError: Video is unavailable
        DownloadError: Download failed

    Examples:
        >>> opts = AudioDownloadOptions(format="m4a", quality="320K")
        >>> info = download_audio("https://youtube.com/watch?v=...", Path("music"), opts)
    """
    options = options or AudioDownloadOptions()
    logger.info(f"Downloading audio: {url}")

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_path / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": options.format,
                "preferredquality": options.quality,
            }
        ],
        "quiet": True,
        "no_warnings": True,
        **options.ydl_opts,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise DownloadError("Download returned no information", url)

            # Determine the final filename (after postprocessing)
            base_filename = ydl.prepare_filename(info)
            downloaded_file = Path(base_filename).with_suffix(f".{options.format}")

            # Parse formats and thumbnails
            formats = _parse_formats(info.get("formats", []))
            thumbnails = _parse_thumbnails(info.get("thumbnails", []))

            video_info = VideoInfo(
                url=url,  # type: ignore[arg-type]
                video_id=info["id"],
                title=info["title"],
                description=info.get("description"),
                uploader=info.get("uploader"),
                uploader_id=info.get("uploader_id"),
                channel=info.get("channel"),
                channel_id=info.get("channel_id"),
                upload_date=info.get("upload_date"),
                timestamp=info.get("timestamp"),
                duration=info.get("duration"),
                view_count=info.get("view_count"),
                like_count=info.get("like_count"),
                comment_count=info.get("comment_count"),
                age_limit=info.get("age_limit", 0),
                is_live=info.get("is_live", False),
                was_live=info.get("was_live", False),
                formats=formats,
                thumbnails=thumbnails,
                categories=info.get("categories", []),
                tags=info.get("tags", []),
                downloaded_file=downloaded_file,
                download_timestamp=datetime.now(),
            )

            logger.info(f"Successfully downloaded audio: {video_info.title}")
            return video_info

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if "unavailable" in error_msg or "private" in error_msg:
            raise UnavailableVideoError(str(e), url) from e
        if "invalid" in error_msg or "url" in error_msg:
            raise InvalidURLError(str(e), url) from e
        raise DownloadError(str(e), url) from e
    except Exception as e:
        raise DownloadError(f"Unexpected error during audio download: {e}", url) from e


def get_transcriptions(url: str, languages: list[str] | None = None) -> list[Transcription]:
    """Extract available subtitles/transcriptions for a video.

    Args:
        url: YouTube video URL
        languages: Language codes to extract (None = all available)

    Returns:
        List of available transcriptions

    Raises:
        InvalidURLError: URL is invalid
        UnavailableVideoError: Video is unavailable
        TranscriptionError: Failed to extract transcriptions

    Examples:
        >>> transcriptions = get_transcriptions("https://youtube.com/watch?v=...")
        >>> for t in transcriptions:
        ...     print(f"{t.language}: {len(t.text)} chars")
    """
    logger.info(f"Extracting transcriptions for: {url}")

    try:
        info = _extract_info(url)

        transcriptions = []

        # Extract manual subtitles
        manual_subs = info.get("subtitles", {})
        for lang, sub_list in manual_subs.items():
            if languages and lang not in languages:
                continue

            # Get the first subtitle format with content
            for sub in sub_list:
                text = sub.get("content", "")
                if text:  # Only include if we have actual content
                    transcriptions.append(
                        Transcription(
                            language=lang,
                            text=text,
                            auto_generated=False,
                            ext=sub.get("ext", "vtt"),
                        )
                    )
                    break  # Use first format with content

        # Extract auto-generated subtitles
        auto_subs = info.get("automatic_captions", {})
        for lang, sub_list in auto_subs.items():
            if languages and lang not in languages:
                continue

            # Get the first subtitle format with content
            for sub in sub_list:
                text = sub.get("content", "")
                if text:  # Only include if we have actual content
                    transcriptions.append(
                        Transcription(
                            language=lang,
                            text=text,
                            auto_generated=True,
                            ext=sub.get("ext", "vtt"),
                        )
                    )
                    break  # Use first format with content

        logger.info(f"Found {len(transcriptions)} transcriptions")
        return transcriptions

    except (InvalidURLError, UnavailableVideoError):
        raise
    except ExtractionError as e:
        raise TranscriptionError(str(e.message), url) from e
    except Exception as e:
        raise TranscriptionError(f"Failed to extract transcriptions: {e}", url) from e
