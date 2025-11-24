"""Dependency injection for YouTube client executor management."""

from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, TypeVar

# Default configuration
DEFAULT_MAX_WORKERS = 5  # Conservative for YouTube API rate limits

_dependencies: dict[str, Callable[[], Any]] = {}

T = TypeVar("T")


def get_default_executor() -> ThreadPoolExecutor:
    """Create default ThreadPoolExecutor for YouTube operations."""
    return ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS, thread_name_prefix="youtube_")


def inject_deps(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to inject executor dependency."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "executor" not in kwargs or kwargs["executor"] is None:
            factory = _dependencies.get("executor", get_default_executor)
            kwargs["executor"] = factory()
        return await func(*args, **kwargs)

    return wrapper


@asynccontextmanager
async def override_dependency(name: str, factory: Callable[[], Any]) -> AsyncIterator[None]:
    """Override a dependency for testing."""
    old_factory = _dependencies.get(name)
    _dependencies[name] = factory
    try:
        yield
    finally:
        if old_factory is not None:
            _dependencies[name] = old_factory
        else:
            _dependencies.pop(name, None)
