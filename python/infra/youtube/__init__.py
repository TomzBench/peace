"""YouTube downloader module."""

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
