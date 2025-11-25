"""Dependency injection for agent module."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar, cast

from anthropic import AsyncAnthropic
from jinja2 import Environment, FileSystemLoader

from python.config.settings import get_settings

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])

# Dependency registry for testing/overrides
_dependency_overrides: dict[str, Callable[[], Any]] = {}


# Dependency factory functions


def get_anthropic_client() -> AsyncAnthropic:
    """Get configured async Anthropic client.

    Raises ValueError if API key is not configured.
    """
    # Check for override first (testing)
    if "client" in _dependency_overrides:
        return cast("AsyncAnthropic", _dependency_overrides["client"]())

    # Get settings (check for override)
    if "settings" in _dependency_overrides:
        settings = _dependency_overrides["settings"]()
    else:
        settings = get_settings()

    # Check if API key is configured
    if not settings.anthropic_api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not configured. Please set it in .env file or environment."
        )

    # Let Anthropic SDK handle validation of API key
    return AsyncAnthropic(
        api_key=settings.anthropic_api_key,
    )


def get_jinja_environment() -> Environment:
    """Get configured Jinja2 environment for template rendering."""
    # Check for override first (testing)
    if "jinja_env" in _dependency_overrides:
        return cast("Environment", _dependency_overrides["jinja_env"]())

    # Set up template directory
    template_dir = Path(__file__).parent

    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    return env


# Dependency injection decorator


def inject_deps(func: F) -> F:
    """Decorator to inject dependencies into function parameters."""
    import inspect

    is_async = inspect.iscoroutinefunction(func)

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        # Inject client if not provided
        if "client" in kwargs and kwargs["client"] is None:
            kwargs["client"] = get_anthropic_client()
        elif "client" not in kwargs:
            sig = inspect.signature(func)
            if "client" in sig.parameters:
                param = sig.parameters["client"]
                # Only inject if default is None
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["client"] = get_anthropic_client()

        # Inject jinja_env if not provided
        if "jinja_env" in kwargs and kwargs["jinja_env"] is None:
            kwargs["jinja_env"] = get_jinja_environment()
        elif "jinja_env" not in kwargs:
            sig = inspect.signature(func)
            if "jinja_env" in sig.parameters:
                param = sig.parameters["jinja_env"]
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["jinja_env"] = get_jinja_environment()

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
            kwargs["client"] = get_anthropic_client()
        elif "client" not in kwargs:
            sig = inspect.signature(func)
            if "client" in sig.parameters:
                param = sig.parameters["client"]
                # Only inject if default is None
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["client"] = get_anthropic_client()

        # Inject jinja_env if not provided
        if "jinja_env" in kwargs and kwargs["jinja_env"] is None:
            kwargs["jinja_env"] = get_jinja_environment()
        elif "jinja_env" not in kwargs:
            sig = inspect.signature(func)
            if "jinja_env" in sig.parameters:
                param = sig.parameters["jinja_env"]
                if param.default is None or param.default == inspect.Parameter.empty:
                    kwargs["jinja_env"] = get_jinja_environment()

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
    """Clear all dependency overrides."""
    _dependency_overrides.clear()
