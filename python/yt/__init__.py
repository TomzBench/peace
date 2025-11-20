"""YouTube downloader module.

A functional wrapper around yt-dlp for downloading videos, audio,
and extracting metadata and transcriptions from YouTube.

Examples:
    Get video information without downloading:
    >>> from python.yt import get_video_info
    >>> info = get_video_info("https://youtube.com/watch?v=...")
    >>> print(f"{info.title} by {info.uploader}")

    Download video:
    >>> from python.yt import download_video
    >>> from pathlib import Path
    >>> info = download_video("https://youtube.com/watch?v=...", Path("downloads"))

    Download audio only:
    >>> from python.yt import download_audio
    >>> info = download_audio(
    ...     "https://youtube.com/watch?v=...",
    ...     Path("music"),
    ...     audio_format="mp3",
    ...     audio_quality="320K"
    ... )

    Get available transcriptions:
    >>> from python.yt import get_transcriptions
    >>> transcriptions = get_transcriptions("https://youtube.com/watch?v=...")
"""

from python.yt.downloader import (
    download_audio,
    download_video,
    get_transcriptions,
    get_video_info,
)
from python.yt.exceptions import (
    DownloadError,
    ExtractionError,
    InvalidURLError,
    TranscriptionError,
    UnavailableVideoError,
    YouTubeError,
)
from python.yt.models import (
    DownloadOptions,
    Format,
    Thumbnail,
    Transcription,
    VideoInfo,
)

__all__ = [
    "DownloadError",
    "DownloadOptions",
    "ExtractionError",
    "Format",
    "InvalidURLError",
    "Thumbnail",
    "Transcription",
    "TranscriptionError",
    "UnavailableVideoError",
    "VideoInfo",
    "YouTubeError",
    "download_audio",
    "download_video",
    "get_transcriptions",
    "get_video_info",
]
