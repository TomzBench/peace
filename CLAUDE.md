## Project Overview

Multi-language project with:
- **Rust workspace** (`crates/cli`, `crates/core`) with PyO3 integration
- **Python FastAPI backend** (`python/api/`) with SQLModel + QDrant vector databases
- **Functional programming approach** - no classes for business logic, pure functions throughout

## Instructions for Claude
- When importing python modules, prefer relative imports
- When writing new python code,
    - write functional style.
    - Inject dependencies like logging or io/network components
- When writing code, make sure all code passes lint and type checks
    - use `uv run mypy python` to check python types
    - use `uv run ruff check` to check lint errors
    - when writing python document comments, avoid examples unless explictly asked for example

## Async Patterns

The project uses asyncio for concurrent operations in several modules:

### YouTube Client (`python/infra/youtube`)
- All client functions are `async def` and use ThreadPoolExecutor for concurrent operations
- Dependency injection pattern for executor management via `dependencies.py`
- Default max_workers=5 (conservative for YouTube API rate limits)
- Functions wrap blocking yt-dlp operations with `loop.run_in_executor()`

### Whisper Client (`python/infra/whisper`)
- Similar async pattern with ThreadPoolExecutor
- Dependency injection for executor management
- Optimized for CPU-bound transcription operations
