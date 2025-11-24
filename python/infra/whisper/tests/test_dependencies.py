"""Tests for dependency injection infrastructure."""

from unittest.mock import Mock

import pytest
from openai import AsyncOpenAI

from ..dependencies import (
    get_openai_client,
    inject_deps,
    override_dependency,
)


def test_get_openai_client_success() -> None:
    """Test creating AsyncOpenAI client with valid API key."""
    # Create mock settings with proper attribute setting
    mock_settings = Mock()
    mock_settings.openai_api_key = "test-key"
    mock_settings.openai_organization = "test-org"

    # Override settings dependency
    with override_dependency("settings", lambda: mock_settings):
        client = get_openai_client()

        assert isinstance(client, AsyncOpenAI)
        assert client.api_key == "test-key"
        assert client.organization == "test-org"


def test_get_openai_client_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing API key raises OpenAIError from SDK."""
    from openai import OpenAIError

    # Remove API key from environment
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Create mock settings with no API key
    mock_settings = Mock()
    mock_settings.openai_api_key = None
    mock_settings.openai_organization = None

    with override_dependency("settings", lambda: mock_settings):
        with pytest.raises(OpenAIError) as exc_info:
            get_openai_client()

        # OpenAI SDK validates the API key
        assert "api_key" in str(exc_info.value).lower()


def test_override_dependency_client() -> None:
    """Test overriding client dependency."""
    mock_client = Mock(spec=AsyncOpenAI)

    with override_dependency("client", lambda: mock_client):
        client = get_openai_client()
        assert client is mock_client

    # After context, should create real client again
    # Create mock settings with proper attribute setting
    mock_settings = Mock()
    mock_settings.openai_api_key = "test-key"
    mock_settings.openai_organization = None

    with override_dependency("settings", lambda: mock_settings):
        client = get_openai_client()
        assert client is not mock_client
        assert isinstance(client, AsyncOpenAI)


def test_inject_deps_decorator_with_client() -> None:
    """Test @inject_deps decorator injects client."""

    @inject_deps
    def test_function(client: AsyncOpenAI | None = None) -> AsyncOpenAI:
        assert client is not None
        return client

    mock_client = Mock(spec=AsyncOpenAI)

    with override_dependency("client", lambda: mock_client):
        result = test_function()
        assert result is mock_client


def test_inject_deps_decorator_with_explicit_client() -> None:
    """Test @inject_deps decorator respects explicitly passed client."""

    @inject_deps
    def test_function(client: AsyncOpenAI | None = None) -> AsyncOpenAI:
        assert client is not None
        return client

    mock_client = Mock(spec=AsyncOpenAI)
    explicit_client = Mock(spec=AsyncOpenAI)

    with override_dependency("client", lambda: mock_client):
        # Explicitly passed client should override DI
        result = test_function(client=explicit_client)
        assert result is explicit_client
        assert result is not mock_client


def test_inject_deps_decorator_without_matching_params() -> None:
    """Test @inject_deps decorator on function without DI parameters."""

    @inject_deps
    def test_function(x: int, y: str) -> str:
        return f"{x}{y}"

    # Should work normally, no injection
    result = test_function(42, "test")
    assert result == "42test"


def test_multiple_overrides() -> None:
    """Test multiple dependency overrides simultaneously."""
    mock_client = Mock(spec=AsyncOpenAI)
    mock_settings = Mock()

    with (
        override_dependency("client", lambda: mock_client),
        override_dependency("settings", lambda: mock_settings),
    ):
        client = get_openai_client()
        assert client is mock_client


def test_nested_overrides() -> None:
    """Test nested dependency overrides."""
    mock_client1 = Mock(spec=AsyncOpenAI)
    mock_client2 = Mock(spec=AsyncOpenAI)

    with override_dependency("client", lambda: mock_client1):
        client = get_openai_client()
        assert client is mock_client1

        # Inner override should take precedence
        with override_dependency("client", lambda: mock_client2):
            client = get_openai_client()
            assert client is mock_client2

        # Outer override restored
        client = get_openai_client()
        assert client is mock_client1
