# Test Fixtures

This directory contains mock data captured from real YouTube videos using yt-dlp.

## Files

- `video_basic.json` - Standard video with basic metadata
- `video_with_subs.json` - Video with subtitles (manual and auto-generated)

## Updating Fixtures

To refresh the mock data from live YouTube:

```bash
python -m python.yt.tests.update_fixtures
```

This will fetch fresh data from YouTube and update the JSON files.

## Why Filesystem Fixtures?

- **Fast tests** - No network calls during test runs
- **Reliable** - Tests work offline and don't depend on YouTube availability
- **Real data** - Fixtures come from actual YouTube responses
- **Updatable** - Easy to refresh when YouTube API changes
