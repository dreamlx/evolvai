"""Adapter for Serena Agent to EvolvAI AgentProtocol.

This adapter isolates EvolvAI from Serena's internal implementation details.
When upstream Serena changes its architecture, only this adapter needs updating.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from serena.agent import SerenaAgent


class SerenaAgentAdapter:
    """Adapts Serena Agent to EvolvAI's AgentProtocol interface.

    This adapter encapsulates all interactions with Serena's internal APIs,
    providing a stable interface for EvolvAI regardless of upstream changes.
    """

    def __init__(self, serena_agent: "SerenaAgent") -> None:
        """Initialize adapter with a Serena Agent instance.

        Args:
            serena_agent: The Serena Agent to adapt

        """
        self._agent = serena_agent

    # LSP Management

    def is_using_language_server(self) -> bool:
        """Check if the agent uses language server-based code analysis."""
        return self._agent.is_using_language_server()

    def is_language_server_running(self) -> bool:
        """Check if any language server is currently running.

        Serena uses a LanguageServerManager that manages multiple LSPs.
        This method checks if at least one is running.
        """
        lsm = self._agent.get_language_server_manager()
        if lsm is None:
            return False
        for ls in lsm.iter_language_servers():
            if ls.is_running():
                return True
        return False

    def reset_language_server(self) -> None:
        """Reset/restart the language server manager."""
        self._agent.reset_language_server_manager()

    def save_lsp_caches(self) -> None:
        """Save all language server caches.

        Serena's LanguageServerManager provides save_all_caches() for this.
        """
        lsm = self._agent.get_language_server_manager()
        if lsm is not None:
            try:
                lsm.save_all_caches()
            except Exception:
                # Silently ignore cache save errors
                pass

    # Project Information

    def has_active_project(self) -> bool:
        """Check if there is an active project."""
        return self._agent._active_project is not None

    def get_project_names(self) -> list[str]:
        """Get list of available project names."""
        return self._agent.serena_config.project_names

    def get_project_root(self) -> str | None:
        """Get the root path of the active project."""
        return self._agent.get_project_root()

    # Tool Management

    def get_active_tool_names(self) -> list[str]:
        """Get list of currently active tool names."""
        return self._agent.get_active_tool_names()

    def record_tool_usage(self, kwargs: dict[str, Any], result: str, tool: Any) -> None:
        """Record tool usage statistics if enabled."""
        if hasattr(self._agent, "record_tool_usage_if_enabled"):
            self._agent.record_tool_usage_if_enabled(kwargs, result, tool)

    def tool_is_active(self, tool_name: str) -> bool:
        """Check if a specific tool is active."""
        return self._agent.tool_is_active(tool_name)

    # Direct access to underlying agent (for cases where full access is needed)

    @property
    def underlying_agent(self) -> "SerenaAgent":
        """Get the underlying Serena Agent.

        Use sparingly - prefer protocol methods for better isolation.
        """
        return self._agent
