"""
Environment Preference Memory - Core component of Serena's intelligent memory system.

This module handles user environment preferences like shell type, Python environment
manager, and other development tool preferences. Following KISS principle with
simple JSON-based storage and clear interfaces.

Focus: AI tool optimization, not generic knowledge storage.
"""

import json
from pathlib import Path
from typing import Any, Optional

from serena.config.serena_config import get_serena_managed_in_project_dir
from serena.constants import SERENA_FILE_ENCODING


class EnvironmentPreferenceMemory:
    """
    Manages user environment preferences for AI tool optimization.

    This is NOT a generic knowledge store - it specifically remembers
    environment configurations to help AI tools generate correct commands
    and configurations.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.memory_dir = Path(get_serena_managed_in_project_dir(project_root)) / "memory" / "environment_config"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.encoding = SERENA_FILE_ENCODING

    def _get_config_path(self, config_type: str) -> Path:
        """Get path for a specific config type file."""
        return self.memory_dir / f"{config_type}.json"

    def _load_config(self, config_type: str) -> dict[str, Any]:
        """Load configuration data for a specific type."""
        config_path = self._get_config_path(config_type)
        if not config_path.exists():
            return {}

        try:
            with open(config_path, encoding=self.encoding) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_config(self, config_type: str, data: dict[str, Any]) -> None:
        """Save configuration data for a specific type."""
        config_path = self._get_config_path(config_type)
        with open(config_path, "w", encoding=self.encoding) as f:
            json.dump(data, f, indent=2)

    # Shell Environment Preferences
    def record_shell_preference(self, shell_type: str, effective_commands: dict[str, str]) -> None:
        """Record shell preference and effective command patterns."""
        config = self._load_config("shell_preferences")
        config["shell_type"] = shell_type
        config["effective_commands"] = effective_commands
        config["last_updated"] = self._get_timestamp()
        self._save_config("shell_preferences", config)

    def get_shell_preference(self) -> Optional[str]:
        """Get user's preferred shell type."""
        config = self._load_config("shell_preferences")
        return config.get("shell_type")

    def get_shell_command(self, generic_command: str) -> str:
        """Get shell-adapted command based on preferences."""
        config = self._load_config("shell_preferences")
        effective_commands = config.get("effective_commands", {})
        return effective_commands.get(generic_command, generic_command)

    # Python Environment Preferences
    def record_python_environment(self, env_manager: str, project_patterns: dict[str, Any]) -> None:
        """Record Python environment manager preference."""
        config = self._load_config("python_environments")
        config["env_manager"] = env_manager
        config["project_patterns"] = project_patterns
        config["last_updated"] = self._get_timestamp()
        self._save_config("python_environments", config)

    def get_python_manager(self, project_path: Optional[str] = None) -> str:
        """Get preferred Python environment manager."""
        if project_path:
            # Check for project-specific preference
            config = self._load_config("python_environments")
            patterns = config.get("project_patterns", {})
            for pattern, manager in patterns.items():
                if pattern in str(project_path):
                    return manager

        # Fall back to global preference
        config = self._load_config("python_environments")
        return config.get("env_manager", "python")  # Default to python

    # Node.js Environment Preferences
    def record_node_environment(self, package_manager: str, build_tool: str) -> None:
        """Record Node.js environment preferences."""
        config = self._load_config("node_environments")
        config["package_manager"] = package_manager
        config["build_tool"] = build_tool
        config["last_updated"] = self._get_timestamp()
        self._save_config("node_environments", config)

    def get_node_package_manager(self) -> str:
        """Get preferred Node.js package manager."""
        config = self._load_config("node_environments")
        return config.get("package_manager", "npm")  # Default to npm

    def get_node_build_tool(self) -> str:
        """Get preferred Node.js build tool."""
        config = self._load_config("node_environments")
        return config.get("build_tool", "webpack")  # Default to webpack

    # Container Runtime Preferences
    def record_container_runtime(self, runtime: str, preferences: dict[str, Any]) -> None:
        """Record container runtime preferences."""
        config = self._load_config("container_runtimes")
        config["runtime"] = runtime
        config["preferences"] = preferences
        config["last_updated"] = self._get_timestamp()
        self._save_config("container_runtimes", config)

    def get_container_runtime(self) -> str:
        """Get preferred container runtime."""
        config = self._load_config("container_runtimes")
        return config.get("runtime", "docker")  # Default to docker

    # Utility Methods
    def _get_timestamp(self) -> str:
        """Get current timestamp for tracking updates."""
        from datetime import datetime

        return datetime.now().isoformat()

    def get_environment_summary(self) -> dict[str, Any]:
        """Get summary of all environment preferences."""
        return {
            "shell": self.get_shell_preference(),
            "python_manager": self.get_python_manager(),
            "node_package_manager": self.get_node_package_manager(),
            "node_build_tool": self.get_node_build_tool(),
            "container_runtime": self.get_container_runtime(),
        }

    def clear_environment_preferences(self) -> None:
        """Clear all environment preferences (for testing/reset)."""
        for config_file in self.memory_dir.glob("*.json"):
            config_file.unlink()
