"""YouTube downloader module.

A functional wrapper around yt-dlp for downloading videos, audio,
and extracting metadata and transcriptions from YouTube.

Examples:
    Get video information without downloading:
    >>> from python.infra.youtube import get_video_info
    >>> info = get_video_info("https://youtube.com/watch?v=...")
    >>> print(f"{info.title} by {info.uploader}")

    Download video:
    >>> from python.infra.youtube import download_video
    >>> from pathlib import Path
    >>> info = download_video("https://youtube.com/watch?v=...", Path("downloads"))

    Download audio only:
    >>> from python.infra.youtube import download_audio
    >>> info = download_audio(
    ...     "https://youtube.com/watch?v=...",
    ...     Path("music"),
    ...     audio_format="mp3",
    ...     audio_quality="320K"
    ... )

    Get available transcriptions:
    >>> from python.infra.youtube import get_transcriptions
    >>> transcriptions = get_transcriptions("https://youtube.com/watch?v=...")
"""

from python.infra.youtube.client import (
    download_audio,
    download_video,
    get_transcriptions,
    get_video_info,
)
from python.infra.youtube.exceptions import (
    DownloadError,
    ExtractionError,
    InvalidURLError,
    TranscriptionError,
    UnavailableVideoError,
    YouTubeError,
)
from python.infra.youtube.models import (
    AudioDownloadOptions,
    Format,
    Thumbnail,
    Transcription,
    VideoDownloadOptions,
    VideoInfo,
)

__all__ = [
    "AudioDownloadOptions",
    "DownloadError",
    "ExtractionError",
    "Format",
    "InvalidURLError",
    "Thumbnail",
    "Transcription",
    "TranscriptionError",
    "UnavailableVideoError",
    "VideoDownloadOptions",
    "VideoInfo",
    "YouTubeError",
    "download_audio",
    "download_video",
    "get_transcriptions",
    "get_video_info",
]
