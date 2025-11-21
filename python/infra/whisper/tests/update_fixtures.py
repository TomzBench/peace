"""Helper script to update test fixtures from real OpenAI Whisper API.

Run this script to fetch fresh transcription data from OpenAI Whisper API.
The data is saved as JSON files in the fixtures/ directory.

Requirements:
    - OpenAI API key must be configured (OPENAI_API_KEY environment variable)
    - Cost: $0.006 per minute of audio transcribed

Usage:
    python -m python.infra.whisper.tests.update_fixtures

TODO: This script is a placeholder. Implementation will be added once an OpenAI API
key is available. The script should:
    1. Create small test audio files (or use existing ones)
    2. Call the actual OpenAI Whisper API to transcribe them
    3. Save the complete API responses as JSON fixtures
    4. Support both transcription and translation endpoints

Example structure (to be implemented):
    - Generate/use test audio files (~5 seconds)
    - Transcribe using transcribe_audio()
    - Translate using transcribe_and_translate()
    - Save results to fixtures/transcription_basic.json
    - Save results to fixtures/transcription_with_translation.json
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def create_test_audio(duration_ms: int, format: str = "mp3") -> bytes:
    """Create test audio data of specified duration.

    Args:
        duration_ms: Audio duration in milliseconds
        format: Audio format (mp3, wav, etc.)

    Returns:
        Audio data as bytes
    """
    from io import BytesIO

    from pydub.generators import Sine  # type: ignore[import-untyped]

    # Generate a simple sine wave tone
    audio = Sine(440).to_audio_segment(duration=duration_ms)
    buffer = BytesIO()
    audio.export(buffer, format=format)
    return buffer.getvalue()


def generate_test_audio_fixtures() -> None:
    """Generate test audio files for integration tests.

    TODO: Implement this to create audio fixtures:
    - short_audio.mp3 (30 seconds)
    - medium_audio.mp3 (5 minutes)
    - long_audio.mp3 (15 minutes)

    These will be used for integration tests to verify real audio processing.
    """
    logger.info("TODO: Generate test audio fixtures")
    # Example implementation (uncomment when ready):
    # fixtures = {
    #     "short_audio.mp3": create_test_audio(30000),
    #     "medium_audio.mp3": create_test_audio(300000),
    #     "long_audio.mp3": create_test_audio(900000),
    # }
    # for name, data in fixtures.items():
    #     fixture_path = FIXTURES_DIR / name
    #     fixture_path.write_bytes(data)
    #     logger.info(f"Created {name} ({len(data)} bytes)")


def generate_whisper_fixtures() -> None:
    """Generate real Whisper API response fixtures.

    TODO: Implement once OpenAI API key is available:
    1. Load/generate small test audio (5-10 seconds)
    2. Call transcribe_audio() with real API
    3. Save TranscriptionResult to fixtures/transcription_basic.json
    4. Test with different models, languages, options

    Cost: ~$0.006 per minute of audio
    """
    logger.info("TODO: Generate Whisper API fixtures")
    # Example implementation (uncomment when ready):
    # from ..client import transcribe_audio
    # from ..audio import open_audio_file
    #
    # # Generate or load test audio
    # test_audio_path = FIXTURES_DIR / "test_audio_5sec.mp3"
    # if not test_audio_path.exists():
    #     test_audio_path.write_bytes(create_test_audio(5000))
    #
    # # Transcribe with real API
    # audio_file = open_audio_file(test_audio_path)
    # result = await transcribe_audio(audio_file)
    #
    # # Save fixture
    # fixture_path = FIXTURES_DIR / "transcription_basic.json"
    # fixture_path.write_text(result.model_dump_json(indent=2))


def main() -> None:
    """Main entry point for fixture generation."""
    logger.info("Whisper Test Fixture Generator")
    logger.info("=" * 50)

    # Ensure fixtures directory exists
    FIXTURES_DIR.mkdir(exist_ok=True)

    # TODO: Uncomment when ready to generate fixtures
    # generate_test_audio_fixtures()
    # generate_whisper_fixtures()

    logger.warning(
        "\nFixture generation is not yet implemented.\n"
        "To implement:\n"
        "1. Uncomment generate_test_audio_fixtures() for audio files\n"
        "2. Configure OPENAI_API_KEY for Whisper API fixtures\n"
        "3. Uncomment generate_whisper_fixtures() for API responses\n"
        "\nSee create_test_audio() function for audio generation logic."
    )


if __name__ == "__main__":
    main()
