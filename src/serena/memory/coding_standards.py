"""
Coding Standards Memory - Core component for learning and applying coding conventions.

This module handles user coding preferences like naming conventions, code style,
and project-specific patterns. Following KISS principle with simple JSON-based storage.

Focus: AI code generation optimization, not generic style guides.
"""

import json
from pathlib import Path
from typing import Any, Optional

from serena.config.serena_config import get_serena_managed_in_project_dir
from serena.constants import SERENA_FILE_ENCODING


class CodingStandardsMemory:
    """
    Manages coding standards and conventions for AI code optimization.

    This learns user's coding preferences to generate code that matches
    their established patterns and conventions.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.memory_dir = Path(get_serena_managed_in_project_dir(project_root)) / "memory" / "coding_standards"
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

    # Naming Conventions
    def record_naming_convention(self, language: str, domain: str, convention: str, examples: Optional[dict[str, str]] = None) -> None:
        """Record naming convention for a specific language and domain."""
        config = self._load_config("naming_conventions")

        key = f"{language}_{domain}"
        config[key] = {"convention": convention, "examples": examples or {}, "last_updated": self._get_timestamp()}

        self._save_config("naming_conventions", config)

    def get_naming_convention(self, language: str, domain: str) -> Optional[str]:
        """Get naming convention for a specific language and domain."""
        config = self._load_config("naming_conventions")
        key = f"{language}_{domain}"
        return config.get(key, {}).get("convention")

    def apply_naming_convention(self, name: str, language: str, domain: str) -> str:
        """Apply naming convention to transform a name."""
        convention = self.get_naming_convention(language, domain)
        if not convention:
            return name  # No convention found, return original

        if convention == "camelCase":
            return self._to_camel_case(name)
        elif convention == "snake_case":
            return self._to_snake_case(name)
        elif convention == "PascalCase":
            return self._to_pascal_case(name)
        elif convention == "kebab-case":
            return self._to_kebab_case(name)

        return name

    # Style Preferences
    def record_style_preference(self, language: str, style_rules: dict[str, Any]) -> None:
        """Record code style preferences for a language."""
        config = self._load_config("style_preferences")
        config[language] = {"rules": style_rules, "last_updated": self._get_timestamp()}
        self._save_config("style_preferences", config)

    def get_style_preferences(self, language: str) -> dict[str, Any]:
        """Get style preferences for a language."""
        config = self._load_config("style_preferences")
        return config.get(language, {}).get("rules", {})

    # Project Patterns
    def record_project_pattern(self, project_type: str, patterns: dict[str, Any]) -> None:
        """Record project-specific coding patterns."""
        config = self._load_config("project_patterns")
        config[project_type] = {"patterns": patterns, "last_updated": self._get_timestamp()}
        self._save_config("project_patterns", config)

    def get_project_patterns(self, project_type: str) -> dict[str, Any]:
        """Get project-specific coding patterns."""
        config = self._load_config("project_patterns")
        return config.get(project_type, {}).get("patterns", {})

    # Utility Methods
    def _get_timestamp(self) -> str:
        """Get current timestamp for tracking updates."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        if "_" in name:
            parts = name.split("_")
            return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])
        elif "-" in name:
            parts = name.split("-")
            return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])
        return name[0].lower() + name[1:] if name else name

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        # Handle camelCase
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
                result.append(char.lower())
            elif char == "-":
                result.append("_")
            else:
                result.append(char.lower())
        return "".join(result)

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        camel = self._to_camel_case(name)
        return camel[0].upper() + camel[1:] if camel else name

    def _to_kebab_case(self, name: str) -> str:
        """Convert name to kebab-case."""
        snake = self._to_snake_case(name)
        return snake.replace("_", "-")

    def detect_domain_from_file(self, file_path: str) -> str:
        """Detect coding domain from file path."""
        file_path_lower = file_path.lower()

        # Frontend detection
        if any(
            pattern in file_path_lower
            for pattern in [
                "frontend",
                "client",
                "ui",
                "components",
                "views",
                "pages",
                "react",
                "vue",
                "angular",
                "jsx",
                "tsx",
                "css",
                "scss",
            ]
        ):
            return "frontend"

        # Backend detection
        if any(
            pattern in file_path_lower
            for pattern in [
                "backend",
                "server",
                "api",
                "models",
                "services",
                "controllers",
                "django",
                "flask",
                "express",
                "fastapi",
                "models.py",
                "views.py",
            ]
        ):
            return "backend"

        # Database detection
        if any(pattern in file_path_lower for pattern in ["database", "db", "models", "schema", "migration", "sql"]):
            return "database"

        # Test detection
        if any(pattern in file_path_lower for pattern in ["test", "tests", "spec", "__tests__", "test_"]):
            return "test"

        # Config detection
        if any(pattern in file_path_lower for pattern in ["config", "settings", "env", "conf"]):
            return "config"

        return "general"

    def get_coding_standards_summary(self) -> dict[str, Any]:
        """Get summary of all coding standards."""
        return {
            "naming_conventions": self._load_config("naming_conventions"),
            "style_preferences": self._load_config("style_preferences"),
            "project_patterns": self._load_config("project_patterns"),
        }

    def clear_coding_standards(self) -> None:
        """Clear all coding standards (for testing/reset)."""
        for config_file in self.memory_dir.glob("*.json"):
            config_file.unlink()
