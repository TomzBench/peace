"""Dependency injection for Whisper module."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar, cast

from openai import AsyncOpenAI

from python.config.settings import get_settings

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])

# Dependency registry for testing/overrides
_dependency_overrides: dict[str, Callable[[], Any]] = {}


# Dependency factory functions


def get_openai_client() -> AsyncOpenAI:
    """Get configured async OpenAI client."""
    # Check for override first (testing)
    if "client" in _dependency_overrides:
        return cast("AsyncOpenAI", _dependency_overrides["client"]())

    # Get settings (check for override)
    if "settings" in _dependency_overrides:
        settings = _dependency_overrides["settings"]()
    else:
        settings = get_settings()

    # Let OpenAI SDK handle validation of API key
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        organization=settings.openai_organization,
    )


# Dependency injection decorator


def inject_deps(func: F) -> F:
    """Decorator to inject dependencies into function parameters."""
    import inspect

    is_async = inspect.iscoroutinefunction(func)

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Inject client if not provided
        if "client" in kwargs and kwargs["client"] is None:
            kwargs["client"] = get_openai_client()
        elif "client" not in kwargs:
            sig = inspect.signature(func)
            if "client" in sig.parameters:
                param = sig.parameters["client"]
                # Only inject if default is None
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["client"] = get_openai_client()

        # Inject settings if not provided
        if "settings" in kwargs and kwargs["settings"] is None:
            kwargs["settings"] = get_settings()
        elif "settings" not in kwargs:
            sig = inspect.signature(func)
            if "settings" in sig.parameters:
                param = sig.parameters["settings"]
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["settings"] = get_settings()

        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Inject client if not provided
        if "client" in kwargs and kwargs["client"] is None:
            kwargs["client"] = get_openai_client()
        elif "client" not in kwargs:
            sig = inspect.signature(func)
            if "client" in sig.parameters:
                param = sig.parameters["client"]
                # Only inject if default is None
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["client"] = get_openai_client()

        # Inject settings if not provided
        if "settings" in kwargs and kwargs["settings"] is None:
            kwargs["settings"] = get_settings()
        elif "settings" not in kwargs:
            sig = inspect.signature(func)
            if "settings" in sig.parameters:
                param = sig.parameters["settings"]
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["settings"] = get_settings()

        return func(*args, **kwargs)

    return async_wrapper if is_async else sync_wrapper  # type: ignore[return-value]


# Testing support


@contextmanager
def override_dependency(name: str, factory: Callable[[], Any]) -> Generator[None, None, None]:
    """Override a dependency for testing."""
    # Save previous override if exists (for nested overrides)
    previous = _dependency_overrides.get(name)
    _dependency_overrides[name] = factory
    try:
        yield
    finally:
        # Restore previous override or remove if there wasn't one
        if previous is not None:
            _dependency_overrides[name] = previous
        else:
            _dependency_overrides.pop(name, None)


def clear_overrides() -> None:
    _dependency_overrides.clear()
