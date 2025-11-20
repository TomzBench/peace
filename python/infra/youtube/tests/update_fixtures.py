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


def fetch_subtitle_content(ydl: Any, url: str, lang: str, formats: list[dict[str, Any]]) -> str:
    """Download and return subtitle content.

    Args:
        ydl: YoutubeDL instance
        url: Video URL
        lang: Language code
        formats: List of subtitle format dicts

    Returns:
        Subtitle content as string
    """
    # Prefer VTT or SRT formats (they contain actual text, not playlists)
    preferred_formats = ["vtt", "srt", "srv3", "json3"]

    # Sort formats to try preferred ones first
    sorted_formats = sorted(
        formats,
        key=lambda f: (
            preferred_formats.index(f.get("ext", ""))
            if f.get("ext") in preferred_formats
            else len(preferred_formats)
        ),
    )

    # Try to download subtitle using yt-dlp
    for fmt in sorted_formats:
        try:
            sub_url = fmt.get("url")
            ext = fmt.get("ext", "unknown")
            if not sub_url:
                continue

            # Download subtitle content
            content: str = ydl.urlopen(sub_url).read().decode("utf-8")

            # Skip m3u8 playlists - we want actual subtitle content
            if content.startswith("#EXTM3U"):
                logger.debug(f"  ⚠ Skipping {lang} {ext} (m3u8 playlist)")
                continue

            logger.info(f"  ✓ Downloaded {lang} subtitle as {ext} ({len(content)} bytes)")
            return content
        except Exception as e:
            logger.debug(f"  ✗ Failed to download {lang} from {ext}: {e}")
            continue

    logger.warning(f"  ⚠ Could not download subtitle for {lang}")
    return ""


def fetch_video_info(url: str) -> dict[str, Any]:
    """Fetch video information from YouTube using yt-dlp.

    Args:
        url: YouTube video URL

    Returns:
        Raw video info dict from yt-dlp with subtitle content included

    Raises:
        Exception: If video fetch fails
    """
    logger.info(f"Fetching video info from: {url}")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "allsubtitles": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise Exception("Failed to extract video information")
            logger.info(f"✓ Fetched: {info['title']}")

            # Download subtitle content and add to fixture
            # Only download a few key languages to keep fixture size reasonable
            key_languages = {"en", "es", "fr", "ja", "de"}
            logger.info(f"Fetching subtitle content for languages: {key_languages}")

            # Process manual subtitles
            if info.get("subtitles"):
                for lang, formats in list(info["subtitles"].items()):
                    # Skip non-key languages
                    base_lang = lang.split("-")[0]  # Handle en-US -> en
                    if base_lang not in key_languages and lang not in key_languages:
                        del info["subtitles"][lang]
                        continue

                    content = fetch_subtitle_content(ydl, url, lang, formats)
                    if content and formats:
                        formats[0]["content"] = content

            # Process automatic captions (limit to key languages only)
            if info.get("automatic_captions"):
                for lang, formats in list(info["automatic_captions"].items()):
                    # Skip non-key languages
                    base_lang = lang.split("-")[0]  # Handle en-US -> en
                    if base_lang not in key_languages and lang not in key_languages:
                        del info["automatic_captions"][lang]
                        continue

                    content = fetch_subtitle_content(ydl, url, f"{lang} (auto)", formats)
                    if content and formats:
                        formats[0]["content"] = content

            return info  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"✗ Failed to fetch {url}: {e}")
        raise


def sanitize_fixture_data(data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize fixture data to remove personal information.

    Args:
        data: Video info dict

    Returns:
        Sanitized data with IP addresses replaced
    """
    import re

    # Convert to JSON string, replace IPs, convert back
    json_str = json.dumps(data, default=str)

    # Replace IP addresses with 0.0.0.0
    # Match patterns like ip=1.2.3.4 or "ip": "1.2.3.4"
    json_str = re.sub(r'ip=\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'ip=0.0.0.0', json_str)
    json_str = re.sub(r'"ip":\s*"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"', '"ip": "0.0.0.0"', json_str)

    return json.loads(json_str)  # type: ignore[no-any-return]


def save_fixture(filename: str, data: dict[str, Any]) -> None:
    """Save fixture data to JSON file.

    Args:
        filename: Name of fixture file (e.g., "video_basic.json")
        data: Video info dict to save
    """
    filepath = FIXTURES_DIR / filename
    logger.info(f"Saving fixture: {filepath}")

    # Sanitize data before saving
    sanitized_data = sanitize_fixture_data(data)

    with open(filepath, "w") as f:
        json.dump(sanitized_data, f, indent=2, default=str)

    logger.info(f"✓ Saved: {filename} ({len(json.dumps(sanitized_data))} bytes) [IP sanitized]")


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
