# Peace API

FastAPI application with YAML configuration, vector database, and user management.

## Quick Start

```bash
# Install dependencies
uv sync

# Run development server
python -m python.infra.api --reload

# Run with custom config
python -m python.infra.api --config prod.yaml
```

## Running the Application

| Command                                                                    | `--config` CLI | Env Vars | YAML File |
|----------------------------------------------------------------------------|----------------|----------|-----------|
| `python -m python.infra.api --config prod.yaml`                            | ✅             | ✅       | ✅        |
| `uvicorn python.infra.api.asgi:app`                                        | ❌             | ✅       | ✅        |
| `gunicorn python.infra.api.asgi:app -w 4 -k uvicorn.workers.UvicornWorker` | ❌             | ✅       | ✅        |

**Use `python -m python.infra.api` when you need `--config`. Use `uvicorn/gunicorn` when you prefer env vars.**

## Development

```bash
# Tests (fast)
uv run pytest

# Tests with coverage
uv run pytest --cov

# Tests with HTML coverage report
uv run pytest --cov --cov-report=html
# Open htmlcov/index.html in browser

# Type checking
uv run mypy python/

# Linting
uv run ruff check .

# update python.infra.youtube.tests test fixtures
python -m python.infra.youtube.tests.update_fixtures --url https://youtube.com/watch?v=...
```

MIT License - see [LICENSE](LICENSE) file for details.

## Development Notes

Parts of this codebase were developed with assistance from Claude (Anthropic).
