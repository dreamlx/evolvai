"""Agent protocol interface for EvolvAI.

This protocol defines the interface that EvolvAI expects from an Agent.
By depending on this protocol instead of concrete implementations,
EvolvAI is isolated from upstream Serena changes.
"""

from typing import Any, Protocol


class AgentProtocol(Protocol):
    """Protocol defining the Agent interface expected by EvolvAI.

    This abstraction layer isolates EvolvAI from Serena's internal implementation.
    When upstream Serena changes, only the Adapter needs to be updated.
    """

    # LSP Management
    def is_using_language_server(self) -> bool:
        """Check if the agent uses language server-based code analysis."""
        ...

    def is_language_server_running(self) -> bool:
        """Check if any language server is currently running."""
        ...

    def reset_language_server(self) -> None:
        """Reset/restart the language server."""
        ...

    def save_lsp_caches(self) -> None:
        """Save all language server caches."""
        ...

    # Project Information
    def has_active_project(self) -> bool:
        """Check if there is an active project."""
        ...

    def get_project_names(self) -> list[str]:
        """Get list of available project names."""
        ...

    def get_project_root(self) -> str | None:
        """Get the root path of the active project."""
        ...

    # Tool Management
    def get_active_tool_names(self) -> list[str]:
        """Get list of currently active tool names."""
        ...

    def record_tool_usage(self, kwargs: dict[str, Any], result: str, tool: Any) -> None:
        """Record tool usage statistics."""
        ...

    def tool_is_active(self, tool_name: str) -> bool:
        """Check if a specific tool is active."""
        ...
