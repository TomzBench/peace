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
