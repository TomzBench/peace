# Claude Code Session Notes

This document captures important conventions, patterns, and lessons learned for this project.

## Project Overview

Multi-language project with:
- **Rust workspace** (`crates/cli`, `crates/core`) with PyO3 integration
- **Python FastAPI backend** (`python/api/`) with SQLModel + QDrant vector databases
- **Functional programming approach** - no classes for business logic, pure functions throughout

## Code Quality Standards

### Always Run Before Committing

```bash
# Linting
uv run ruff check

# Type checking
uv run mypy python

# Tests (aim for 90%+ coverage)
uv run pytest python/api/tests/ -v
```

All three must pass with zero errors.

## Architecture Patterns

### 1. Dataclass vs Pydantic BaseModel

**Choose the right tool for data modeling:**

**Use Pydantic `BaseModel` for:**
- ✅ API response models (data from external APIs)
- ✅ Database entities (SQLModel)
- ✅ Data requiring validation, serialization, or type coercion
- Examples: `VideoInfo`, `Segment`, `TranscriptionResult`, `User`, `Video`

**Use `@dataclass` for:**
- ✅ Configuration/options objects (simple parameter grouping)
- ✅ Internal data structures without validation needs
- Examples: `VideoDownloadOptions`, `AudioDownloadOptions`, `TranscriptionOptions`

**Why this matters:**
- BaseModel: Validation + serialization, but heavier
- @dataclass: Lightweight + simple, but no validation

```python
# ✅ DO: API response with validation
class VideoInfo(BaseModel):
    video_id: str
    title: str
    duration: int | None = None

# ✅ DO: Simple options without validation
@dataclass
class VideoDownloadOptions:
    format: str = "best"
    ydl_opts: dict[str, Any] = field(default_factory=dict)

# ❌ DON'T: BaseModel for simple config (overkill)
class DownloadOptions(BaseModel):
    format: str = "best"
```

**Last audited: 2025-11-20** - All models follow this pattern consistently.

### 2. Functional Approach (NOT Class-Based)

**DO** ✅
```python
# Pure functions with explicit dependencies
async def create_user(
    session: AsyncSession,
    email: str,
    username: str,
    hashed_password: str,
) -> User:
    user = User(email=email, username=username, ...)
    session.add(user)
    await session.commit()
    return user
```

**DON'T** ❌
```python
# Avoid classes for CRUD/repositories
class UserRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, user):
        ...
```

**Why**: Small project with few models. Functional approach is simpler, more explicit, and easier to test.

### 3. FastAPI Dependency Injection

**DO** ✅ Modern pattern with `Annotated`
```python
from typing import Annotated
from fastapi import Depends

# Module-level type alias
SessionDep = Annotated[AsyncSession, Depends(get_session)]

@router.post("/users/")
async def create_user(
    user_data: UserCreate,
    session: SessionDep,  # Clean!
):
    ...
```

**DON'T** ❌ Function calls in defaults
```python
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),  # Code smell!
):
    ...
```

**Why**: Function calls in default arguments are evaluated at definition time. `Annotated` is the modern FastAPI pattern and avoids linting warnings.

### 4. SQLModel Schema Pattern

**Unified approach** (less boilerplate for small projects):

```python
# models/user.py
class User(SQLModel, table=True):
    """Database model."""
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    ...

class UserCreate(SQLModel):
    """API input schema."""
    email: str
    password: str

class UserRead(SQLModel):
    """API output schema (no password!)."""
    id: int
    email: str
    # No password field!
```

**Why**: Small project benefits from reduced boilerplate. Split into separate schemas only when needed for security/flexibility.

## Project Structure

```
python/api/
├── models/           # SQLModel definitions
│   └── user.py       # User + UserCreate/Update/Read
├── crud/             # Pure functions for database operations
│   └── user.py       # create_user(), get_user_by_id(), etc.
├── routes/           # FastAPI endpoints
│   └── users.py      # REST API handlers
├── db/               # Database setup (functional)
│   ├── sql.py        # SQLModel/SQLAlchemy async engine
│   ├── vector.py     # QDrant clients (2 databases)
│   └── session.py    # Lifecycle functions
├── tests/
│   ├── test_db.py           # Generic DB infrastructure
│   ├── test_user.py         # User model/schema tests
│   ├── test_user_crud.py    # User CRUD operation tests
│   └── test_user_routes.py  # User API endpoint tests
├── config.py         # Pydantic settings
├── security.py       # Password hashing utilities
└── main.py           # FastAPI app
```

### Adding New Models

When adding a new model (e.g., `Post`):

1. Create `models/post.py` (model + schemas)
2. Create `crud/post.py` (pure CRUD functions)
3. Import model in `db/sql.py` (for table creation)
4. Create `tests/test_post.py` (model tests)
5. Create `tests/test_post_crud.py` (CRUD tests)
6. Create `routes/posts.py` (optional, when needed)
7. Create `tests/test_post_routes.py` (API tests)

## Testing Strategy

### Separate Concerns

- **`test_db.py`** - Generic database infrastructure (stays small!)
- **`test_<model>.py`** - Model instantiation, defaults, schemas, constraints
- **`test_<model>_crud.py`** - CRUD operations (create, read, update, delete)
- **`test_<model>_routes.py`** - API endpoints (HTTP requests/responses)

### Coverage Goal: 90%+

Run tests with coverage:
```bash
uv run pytest --cov=python/api --cov-report=term-missing
```

## Common Pitfalls & Solutions

### ❌ Mypy Error: "cannot find implementation or library stub for module"

**Problem**: LSP/mypy can't find packages in venv

**Solution**: Configure in `~/.dotfiles/nvim/after/plugin/lsp.lua`:
```lua
vim.lsp.config("pylsp", {
    settings = {
        pylsp = {
            plugins = {
                jedi = {
                    environment = vim.fn.getcwd() .. "/.venv/bin/python",
                    extra_paths = { vim.fn.getcwd() .. "/.venv/lib/python3.11/site-packages" }
                },
                pylsp_mypy = {
                    overrides = {
                        "--python-executable", vim.fn.getcwd() .. "/.venv/bin/python", true
                    },
                },
            }
        }
    },
})
```

### ❌ Mypy: "module shadows library module"

**Problem**: Adding site-packages to `mypy_path` causes shadowing errors

**Solution**: DON'T add site-packages to mypy_path! Use `--python-executable` instead:
```toml
# pyproject.toml
[tool.mypy]
mypy_path = "."  # NOT ".:.venv/lib/python3.11/site-packages"
```

Configure pylsp_mypy to use venv Python (see above).

### ❌ Type Error: "Argument has incompatible type 'int | None'; expected 'int'"

**Problem**: Model IDs are `int | None` before persistence, but functions expect `int`

**Solution**: Add assertions in tests after creating records:
```python
created_user = await create_user(...)
assert created_user.id is not None  # Type narrowing
user = await get_user_by_id(session, created_user.id)  # Now OK
```

## Configuration Notes

### Ruff

- Configured in `pyproject.toml`
- Auto-fix enabled
- Allow unused imports in `__init__.py` (F401)

### Mypy

- Strict mode enabled
- Use `extra_checks = true` (not deprecated `strict_concatenate`)
- Ignore missing imports for: `qdrant_client`, `sqlmodel`, `alembic`

### Pytest

- Async mode: auto
- Test path: `python/api/tests`
- Use `pytest-asyncio` for async tests

## Database Configuration

### Two Database Types

1. **SQL Database** (SQLModel/SQLAlchemy)
   - Single instance
   - Default: `sqlite+aiosqlite:///./peace.db`
   - For structured data (users, resources, etc.)

2. **Vector Databases** (QDrant)
   - Two instances: `db1` and `db2`
   - URLs: `localhost:6333` and `localhost:6334`
   - For embeddings and similarity search

### Accessing Databases

```python
# SQL
from python.api.db import get_session
async def endpoint(session: SessionDep):
    user = await get_user_by_id(session, user_id)

# Vector
from python.api.db import get_vector_db
async def search(query: str):
    db1 = get_vector_db("db1")
    results = await db1.search(...)
```

## Development Workflow

1. **Start development server**:
   ```bash
   uv run uvicorn python.api.main:app --reload
   ```

2. **Make changes** (following functional patterns)

3. **Write tests** (aim for 90%+ coverage)

4. **Run checks** (ruff, mypy, pytest)

5. **Commit** when all checks pass

## IDE Setup (Neovim + pylsp)

Using:
- `pylsp` for language server (completions, goto definition)
- `pylsp_mypy` plugin for type checking
- `ruff` LSP for linting/formatting

Key: Configure pylsp to use project's venv Python (see "Common Pitfalls" above).

## Python Version & Dependencies

- **Python**: 3.11+
- **Package manager**: `uv`
- **Main dependencies**: FastAPI, SQLModel, QDrant client, Pydantic
- **Dev dependencies**: pytest, pytest-asyncio, httpx, ruff, mypy

## Remember

- Functional > Classes (for this small project)
- Explicit > Implicit (pass dependencies, no hidden state)
- Tests are documentation (write them well)
- Type hints everywhere (mypy strict mode)
- 90%+ coverage is the goal, not a suggestion

---

*This document should be updated as new patterns emerge or conventions change.*
