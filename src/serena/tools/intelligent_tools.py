"""
Intelligent Tools - AI Tool Optimization Components

These tools use Serena's intelligent memory system to provide optimized
command generation and tool selection based on learned user preferences.

This is the replacement for generic memory tools - focused on AI tool optimization.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from serena.memory.environment_preferences import EnvironmentPreferenceMemory
from serena.tools import Tool


class DetectEnvironmentTool(Tool):
    """
    Detect and record user's development environment preferences.

    This tool helps Serena learn the user's environment setup for better
    command generation and tool selection in future interactions.
    """

    def apply(self) -> str:
        """
        Detect current environment and record preferences.

        Analyzes shell type, Python environment, Node.js setup, etc.
        and records them for future AI tool optimization.
        """
        # Get environment preference memory for current project
        env_memory = EnvironmentPreferenceMemory(self.project.project_root)

        detected_info = {}

        # Detect shell type
        shell = self._detect_shell_type()
        if shell:
            env_memory.record_shell_preference(shell, self._get_effective_shell_commands(shell))
            detected_info["shell"] = shell

        # Detect Python environment
        python_manager = self._detect_python_manager()
        if python_manager:
            env_memory.record_python_environment(python_manager, {})
            detected_info["python_manager"] = python_manager

        # Detect Node.js environment if applicable
        node_info = self._detect_node_environment()
        if node_info:
            env_memory.record_node_environment(node_info["package_manager"], node_info["build_tool"])
            detected_info.update(node_info)

        # Detect container runtime
        container_runtime = self._detect_container_runtime()
        if container_runtime:
            env_memory.record_container_runtime(container_runtime, {})
            detected_info["container_runtime"] = container_runtime

        return json.dumps(
            {
                "status": "Environment preferences recorded",
                "detected": detected_info,
                "message": "Serena will use these preferences for optimized command generation",
            },
            indent=2,
        )

    def _detect_shell_type(self) -> Optional[str]:
        """Detect current shell type."""
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            return "zsh"
        elif "bash" in shell:
            return "bash"
        elif "fish" in shell:
            return "fish"
        return None

    def _get_effective_shell_commands(self, shell_type: str) -> dict:
        """Get shell-specific effective commands."""
        commands = {}

        if shell_type == "zsh":
            commands.update(
                {
                    "run_test": "uv run poe test",
                    "format": "uv run poe format",
                    "type_check": "uv run poe type-check",
                }
            )
        elif shell_type == "bash":
            commands.update(
                {
                    "run_test": "poe test",
                    "format": "poe format",
                    "type_check": "poe type-check",
                }
            )

        return commands

    def _detect_python_manager(self) -> Optional[str]:
        """Detect Python environment manager."""
        project_root = Path(self.project.project_root)

        # Check for uv configuration
        if (project_root / "pyproject.toml").exists():
            try:
                with open(project_root / "pyproject.toml") as f:
                    content = f.read()
                    if "[tool.poe]" in content or "[tool.uv]" in content:
                        return "uv"
            except OSError:
                pass

        # Check for uv lock file
        if (project_root / "uv.lock").exists():
            return "uv"

        # Check for poetry
        if (project_root / "poetry.lock").exists():
            return "poetry"

        # Check for pipenv
        if (project_root / "Pipfile").exists():
            return "pipenv"

        return "python"  # Default

    def _detect_node_environment(self) -> Optional[dict]:
        """Detect Node.js environment if applicable."""
        project_root = Path(self.project.project_root)

        # Look for package.json
        package_json = project_root / "package.json"
        if not package_json.exists():
            return None

        node_info = {}

        # Detect package manager
        if (project_root / "package-lock.json").exists():
            node_info["package_manager"] = "npm"
        elif (project_root / "yarn.lock").exists():
            node_info["package_manager"] = "yarn"
        elif (project_root / "pnpm-lock.yaml").exists():
            node_info["package_manager"] = "pnpm"
        else:
            node_info["package_manager"] = "npm"  # Default

        # Detect build tool (simplified)
        if (project_root / "vite.config.js").exists() or (project_root / "vite.config.ts").exists():
            node_info["build_tool"] = "vite"
        elif (project_root / "webpack.config.js").exists():
            node_info["build_tool"] = "webpack"
        else:
            node_info["build_tool"] = "unknown"

        return node_info

    def _detect_container_runtime(self) -> Optional[str]:
        """Detect container runtime preference."""
        # Simple detection based on available commands

        if shutil.which("docker"):
            return "docker"
        elif shutil.which("podman"):
            return "podman"

        return None


class GenerateOptimizedCommandTool(Tool):
    """
    Generate commands optimized for user's environment preferences.

    This tool uses learned environment preferences to generate commands
    that are compatible with the user's specific development setup.
    """

    def apply(self, intent: str, context: Optional[str] = None) -> str:
        """
        Generate optimized command based on intent and learned preferences.

        Args:
            intent: Description of the desired action (e.g., "run tests", "format code")
            context: Additional context for command generation

        """
        env_memory = EnvironmentPreferenceMemory(self.project.project_root)

        # Get user's environment preferences
        shell_type = env_memory.get_shell_preference()
        python_manager = env_memory.get_python_manager()

        # Generate command based on intent
        command = self._generate_command_for_intent(intent, env_memory)

        return json.dumps(
            {
                "intent": intent,
                "command": command,
                "environment": {
                    "shell": shell_type,
                    "python_manager": python_manager,
                },
                "optimization_applied": bool(command != self._get_generic_command(intent)),
            },
            indent=2,
        )

    def _generate_command_for_intent(self, intent: str, env_memory: EnvironmentPreferenceMemory) -> str:
        """Generate optimized command for specific intent."""
        intent_lower = intent.lower()

        # Test-related commands
        if any(word in intent_lower for word in ["test", "tests", "testing"]):
            python_manager = env_memory.get_python_manager()
            if python_manager == "uv":
                return "uv run poe test"
            elif python_manager == "poetry":
                return "poetry run pytest"
            else:
                return "pytest"

        # Format-related commands
        elif any(word in intent_lower for word in ["format", "formatting", "lint"]):
            python_manager = env_memory.get_python_manager()
            if python_manager == "uv":
                return "uv run poe format"
            elif python_manager == "poetry":
                return "poetry run ruff check --fix . && poetry run black ."
            else:
                return "ruff check --fix . && black ."

        # Type checking commands
        elif any(word in intent_lower for word in ["type", "types", "mypy", "check"]):
            python_manager = env_memory.get_python_manager()
            if python_manager == "uv":
                return "uv run poe type-check"
            elif python_manager == "poetry":
                return "poetry run mypy"
            else:
                return "mypy"

        # Build commands
        elif any(word in intent_lower for word in ["build", "compile"]):
            python_manager = env_memory.get_python_manager()
            if python_manager == "uv":
                return "uv build"
            elif python_manager == "poetry":
                return "poetry build"
            else:
                return "python -m build"

        # Fallback to generic command
        return self._get_generic_command(intent)

    def _get_generic_command(self, intent: str) -> str:
        """Get generic command as fallback."""
        intent_lower = intent.lower()

        if "test" in intent_lower:
            return "pytest"
        elif "format" in intent_lower:
            return "ruff check --fix . && black ."
        elif "type" in intent_lower:
            return "mypy"
        elif "build" in intent_lower:
            return "python -m build"
        else:
            return f"# Command for '{intent}' not recognized"


class ShowEnvironmentPreferencesTool(Tool):
    """
    Show current environment preferences learned by Serena.

    This tool displays the environment preferences that Serena has learned
    for optimizing AI tool usage.
    """

    def apply(self) -> str:
        """
        Show current environment preferences.
        """
        env_memory = EnvironmentPreferenceMemory(self.project.project_root)
        summary = env_memory.get_environment_summary()

        return json.dumps(
            {"environment_preferences": summary, "message": "These preferences are used to optimize AI tool commands and selections"},
            indent=2,
        )
