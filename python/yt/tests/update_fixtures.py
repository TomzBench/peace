"""Helper script to update test fixtures from live YouTube data.

Run this script to fetch fresh mock data from YouTube using yt-dlp.
The data is saved as JSON files in the fixtures/ directory.

Usage:
    python -m python.yt.tests.update_fixtures
    python -m python.yt.tests.update_fixtures --url https://youtube.com/watch?v=...
"""

import json
import logging
from pathlib import Path
from typing import Any

import yt_dlp  # type: ignore[import-untyped]

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Default test videos
DEFAULT_VIDEOS = {
    "video_basic.json": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley
    "video_with_subs.json": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo
}


def fetch_video_info(url: str) -> dict[str, Any]:
    """Fetch video information from YouTube using yt-dlp.

    Args:
        url: YouTube video URL

    Returns:
        Raw video info dict from yt-dlp

    Raises:
        Exception: If video fetch fails
    """
    logger.info(f"Fetching video info from: {url}")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise Exception("Failed to extract video information")
            logger.info(f"✓ Fetched: {info['title']}")
            return info  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"✗ Failed to fetch {url}: {e}")
        raise


def save_fixture(filename: str, data: dict[str, Any]) -> None:
    """Save fixture data to JSON file.

    Args:
        filename: Name of fixture file (e.g., "video_basic.json")
        data: Video info dict to save
    """
    filepath = FIXTURES_DIR / filename
    logger.info(f"Saving fixture: {filepath}")

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"✓ Saved: {filename} ({len(json.dumps(data))} bytes)")


def update_all_fixtures() -> None:
    """Update all default test fixtures."""
    logger.info("Updating test fixtures from live YouTube\n")

    success_count = 0
    fail_count = 0

    for filename, url in DEFAULT_VIDEOS.items():
        try:
            info = fetch_video_info(url)
            save_fixture(filename, info)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to update {filename}: {e}")
            fail_count += 1
        print()  # Blank line between videos

    logger.info("=" * 60)
    logger.info(f"Results: {success_count} succeeded, {fail_count} failed")


def update_custom_fixture(url: str, filename: str | None = None) -> None:
    """Update a specific fixture from a custom URL.

    Args:
        url: YouTube video URL
        filename: Optional custom filename (auto-generated if None)
    """
    if filename is None:
        # Extract video ID from URL for filename
        video_id = url.split("v=")[-1].split("&")[0]
        filename = f"video_{video_id}.json"

    logger.info(f"Updating custom fixture: {filename}")
    info = fetch_video_info(url)
    save_fixture(filename, info)
    logger.info("✓ Done")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Update test fixtures from live YouTube data")
    parser.add_argument(
        "--url",
        type=str,
        help="Custom YouTube URL to fetch (saves as video_<id>.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output filename (use with --url)",
    )

    args = parser.parse_args()

    if args.url:
        update_custom_fixture(args.url, args.output)
    else:
        update_all_fixtures()


if __name__ == "__main__":
    main()
