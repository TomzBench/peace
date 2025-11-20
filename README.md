# Peace API

FastAPI application with YAML configuration, vector database, and user management.

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server
python -m python.api --reload

# Run with custom config
python -m python.api --config prod.yaml
```

## Running the Application

| Command                                                              | `--config` CLI | Env Vars | YAML File |
|----------------------------------------------------------------------|----------------|----------|-----------|
| `python -m python.api --config prod.yaml`                            | ✅             | ✅       | ✅        |
| `uvicorn python.api.asgi:app`                                        | ❌             | ✅       | ✅        |
| `gunicorn python.api.asgi:app -w 4 -k uvicorn.workers.UvicornWorker` | ❌             | ✅       | ✅        |

**Use `python -m python.api` when you need `--config`. Use `uvicorn/gunicorn` when you prefer env vars.**

## Development

```bash
# Tests
uv run pytest

# Tests with coverage (terminal report)
uv run pytest --cov=python/api --cov-report=term-missing

# Tests with coverage (HTML report)
uv run pytest --cov=python/api --cov-report=html
# Open htmlcov/index.html in browser

# Type checking
uv run mypy python/

# Linting
uv run ruff check .
```
