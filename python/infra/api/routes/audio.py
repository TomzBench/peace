import logging

from fastapi import APIRouter

from python.infra.api.dependencies import SettingsDepClean
from python.infra.whisper import Transcription, open_audio_file_async, transcribe_audio
from python.infra.youtube import download_audio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/summary/{video_id}", response_model=Transcription)
async def transcribe_video(video_id: str, settings: SettingsDepClean) -> Transcription:
    audio_path = settings.downloads_dir / f"{video_id}.mp3"
    await download_audio(video_id, settings.downloads_dir)
    audio_file = await open_audio_file_async(audio_path)
    result = await transcribe_audio(audio_file)
    return result
