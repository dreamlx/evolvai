"""
Serena Intelligent Memory System - Unified AI Tool Optimization

This module coordinates all intelligent memory components to provide
unified AI tool optimization capabilities.

Core Components Integrated:
- EnvironmentPreferenceMemory: Shell, Python, Node.js preferences
- CodingStandardsMemory: Naming conventions, code style preferences
- ProjectContextMemory: Project feature associations and learning

Design Philosophy: KISS principle - simple, effective, focused on AI tool optimization.
"""

import json
from pathlib import Path
from typing import Any, Optional

from serena.config.serena_config import get_serena_managed_in_project_dir
from serena.constants import SERENA_FILE_ENCODING
from serena.memory.coding_standards import CodingStandardsMemory
from serena.memory.environment_preferences import EnvironmentPreferenceMemory


class SerenaIntelligentMemory:
    """
    Unified intelligent memory system for AI tool optimization.

    This class coordinates all memory components to provide:
    - Environment-aware command generation
    - Coding standards application
    - Project context understanding
    - Learning from user interactions
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.memory_dir = Path(get_serena_managed_in_project_dir(project_root)) / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Core memory components
        self.env_memory = EnvironmentPreferenceMemory(project_root)
        self.standards_memory = CodingStandardsMemory(project_root)

        # Learning cache
        self.learning_cache = self.memory_dir / "learning_cache.json"
        self._load_learning_cache()

    def _load_learning_cache(self) -> None:
        """Load learning cache from storage."""
        if self.learning_cache.exists():
            try:
                with open(self.learning_cache, encoding=SERENA_FILE_ENCODING) as f:
                    self._cache = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._cache = {}
        else:
            self._cache = {}

    def _save_learning_cache(self) -> None:
        """Save learning cache to storage."""
        with open(self.learning_cache, "w", encoding=SERENA_FILE_ENCODING) as f:
            json.dump(self._cache, f, indent=2)

    def get_optimal_configuration(self, operation: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Get optimal configuration for a specific operation.

        Args:
            operation: Description of the desired operation
            context: Additional context (file_path, language, etc.)

        Returns:
            Optimal configuration including environment, coding standards, and tools

        """
        config = {
            "operation": operation,
            "environment": self._get_environment_config(),
            "coding_standards": self._get_coding_standards_config(context),
            "learned_preferences": self._get_learned_preferences(operation, context),
        }

        return config

    def _get_environment_config(self) -> dict[str, Any]:
        """Get environment configuration."""
        return {
            "shell": self.env_memory.get_shell_preference(),
            "python_manager": self.env_memory.get_python_manager(),
            "node_package_manager": self.env_memory.get_node_package_manager(),
            "container_runtime": self.env_memory.get_container_runtime(),
        }

    def _get_coding_standards_config(self, context: dict[str, Any]) -> dict[str, Any]:
        """Get coding standards configuration."""
        language = context.get("language", "unknown")
        file_path = context.get("file_path", "")

        if file_path:
            domain = self.standards_memory.detect_domain_from_file(file_path)
        else:
            domain = "general"

        return {
            "language": language,
            "domain": domain,
            "naming_convention": self.standards_memory.get_naming_convention(language, domain),
            "style_preferences": self.standards_memory.get_style_preferences(language),
        }

    def _get_learned_preferences(self, operation: str, context: dict[str, Any]) -> dict[str, Any]:
        """Get learned preferences for the operation."""
        # Simple cache-based learning - can be extended with ML in future
        cache_key = f"{operation}_{context.get('language', 'unknown')}"
        return self._cache.get(cache_key, {})

    def learn_from_interaction(self, operation: str, context: dict[str, Any], result: dict[str, Any]) -> None:
        """
        Learn from user interaction to improve future recommendations.

        Args:
            operation: The operation performed
            context: Context of the operation
            result: Result and user feedback

        """
        # Simple learning - record successful patterns
        if result.get("success", False):
            cache_key = f"{operation}_{context.get('language', 'unknown')}"
            self._cache[cache_key] = {
                "last_used": self._get_timestamp(),
                "success_count": self._cache.get(cache_key, {}).get("success_count", 0) + 1,
                "configuration": result.get("configuration", {}),
            }
            self._save_learning_cache()

    def generate_optimized_command(self, intent: str, context: Optional[dict[str, Any]] = None) -> str:
        """
        Generate optimized command based on intent and learned preferences.

        Args:
            intent: Description of desired action
            context: Optional context for command generation

        Returns:
            Optimized command string

        """
        if context is None:
            context = {}

        # Get optimal configuration
        config = self.get_optimal_configuration(intent, context)

        # Generate command based on environment preferences
        command = self._generate_command_from_config(intent, config)

        return command

    def _generate_command_from_config(self, intent: str, config: dict[str, Any]) -> str:
        """Generate command from configuration."""
        env_config = config["environment"]
        python_manager = env_config.get("python_manager", "python")

        intent_lower = intent.lower()

        # Test commands
        if any(word in intent_lower for word in ["test", "tests", "testing"]):
            if python_manager == "uv":
                return "uv run poe test"
            elif python_manager == "poetry":
                return "poetry run pytest"
            else:
                return "pytest"

        # Format commands
        elif any(word in intent_lower for word in ["format", "formatting", "lint"]):
            if python_manager == "uv":
                return "uv run poe format"
            elif python_manager == "poetry":
                return "poetry run ruff check --fix . && poetry run black ."
            else:
                return "ruff check --fix . && black ."

        # Type checking commands
        elif any(word in intent_lower for word in ["type", "types", "mypy", "check"]):
            if python_manager == "uv":
                return "uv run poe type-check"
            elif python_manager == "poetry":
                return "poetry run mypy"
            else:
                return "mypy"

        # Build commands
        elif any(word in intent_lower for word in ["build", "compile"]):
            if python_manager == "uv":
                return "uv build"
            elif python_manager == "poetry":
                return "poetry build"
            else:
                return "python -m build"

        return f"# Command for '{intent}' not recognized"

    def apply_coding_standards(self, code: str, context: dict[str, Any]) -> str:
        """
        Apply coding standards to generated code.

        Args:
            code: Code to transform
            context: Context including language and file path

        Returns:
            Transformed code matching project standards

        """
        language = context.get("language", "unknown")
        file_path = context.get("file_path", "")

        # Detect domain from file context
        if file_path:
            domain = self.standards_memory.detect_domain_from_file(file_path)
        else:
            domain = "general"

        # Apply naming conventions
        convention = self.standards_memory.get_naming_convention(language, domain)
        if convention:
            code = self._apply_naming_convention(code, convention, self.standards_memory)

        # Apply style preferences if available
        style_preferences = self.standards_memory.get_style_preferences(language)
        if style_preferences:
            # This is a placeholder for style application
            pass

        return code

    def _apply_naming_convention(self, code: str, convention: str, standards_memory: CodingStandardsMemory) -> str:
        """Apply naming convention to code (simplified implementation)."""
        lines = code.split("\n")
        transformed_lines = []

        for line in lines:
            transformed_line = self._transform_line_naming(line, convention, standards_memory)
            transformed_lines.append(transformed_line)

        return "\n".join(transformed_lines)

    def _transform_line_naming(self, line: str, convention: str, standards_memory: CodingStandardsMemory) -> str:
        """Transform naming in a single line (simplified)."""
        import re

        # Simple pattern matching for function definitions
        if "def " in line:
            func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if func_match:
                func_name = func_match.group(1)
                new_name = standards_memory.apply_naming_convention(func_name, "python", "general")
                line = line.replace(f"def {func_name}", f"def {new_name}")

        return line

    def get_memory_summary(self) -> dict[str, Any]:
        """Get summary of all intelligent memory components."""
        return {
            "environment_preferences": self.env_memory.get_environment_summary(),
            "coding_standards": self.standards_memory.get_coding_standards_summary(),
            "learning_cache_size": len(self._cache),
            "last_updated": self._get_timestamp(),
        }

    def clear_all_memory(self) -> None:
        """Clear all intelligent memory (for testing/reset)."""
        self.env_memory.clear_environment_preferences()
        self.standards_memory.clear_coding_standards()
        self._cache = {}
        self._save_learning_cache()

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()
