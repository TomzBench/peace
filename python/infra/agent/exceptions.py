"""Custom exceptions for agent-related operations."""


class AgentError(Exception):
    """Base exception for all agent-related errors."""

    def __init__(self, message: str, context: dict[str, str] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation with context if available."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (context: {context_str})"
        return self.message


class SummarizationError(AgentError):
    """Raised when transcript summarization fails."""


class TemplateRenderError(AgentError):
    """Raised when template rendering fails."""


class PDFGenerationError(AgentError):
    """Raised when PDF generation fails."""
