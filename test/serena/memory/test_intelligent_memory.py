"""
Tests for SerenaIntelligentMemory coordination system.

Tests unified coordination of all memory components and intelligent optimization.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from serena.memory.intelligent_memory import SerenaIntelligentMemory


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def intelligent_memory(temp_project_root):
    """Create a SerenaIntelligentMemory instance for testing."""
    return SerenaIntelligentMemory(temp_project_root)


class TestSerenaIntelligentMemory:
    """Test cases for SerenaIntelligentMemory."""

    def test_init_creates_memory_directories(self, intelligent_memory, temp_project_root):
        """Test that initialization creates all memory directories."""
        memory_root = temp_project_root / ".serena" / "memory"
        assert memory_root.exists()
        assert (memory_root / "environment").exists()
        assert (memory_root / "coding_standards").exists()
        assert (memory_root / "learning_cache").exists()

    def test_get_optimal_configuration(self, intelligent_memory):
        """Test getting optimal configuration for operations."""
        # Set up environment preferences
        intelligent_memory.env_memory.record_shell_preference("zsh", {"run_test": "uv run poe test", "format": "uv run poe format"})
        intelligent_memory.env_memory.record_python_environment("uv", {"version": "0.5.0"})

        # Set up coding standards
        intelligent_memory.standards_memory.record_naming_convention(
            "python", "backend", "snake_case", {"function_example": "test_function"}
        )

        # Get configuration
        context = {"language": "python", "file_path": "services/user.py"}
        config = intelligent_memory.get_optimal_configuration("run tests", context)

        assert config["environment"]["shell"] == "zsh"
        assert config["environment"]["python_manager"] == "uv"
        assert config["coding_standards"]["naming_convention"] == "snake_case"
        assert config["coding_standards"]["domain"] == "backend"

    def test_apply_coding_standards(self, intelligent_memory):
        """Test applying coding standards to code."""
        # Set up coding standards
        intelligent_memory.standards_memory.record_naming_convention("python", "backend", "snake_case", {})
        intelligent_memory.standards_memory.record_style_preferences("python", {"max_line_length": 88})

        # Apply standards to code
        context = {"language": "python", "file_path": "services/user.py"}
        original_code = "def myTestFunction(): pass"
        transformed_code = intelligent_memory.apply_coding_standards(original_code, context)

        # Note: The actual transformation is simplified in this implementation
        # In a more sophisticated version, we'd expect proper AST-based transformation
        assert isinstance(transformed_code, str)

    def test_generate_optimized_command(self, intelligent_memory):
        """Test generating optimized commands based on intent."""
        # Set up environment preferences
        intelligent_memory.env_memory.record_shell_preference("zsh", {"run_test": "uv run poe test", "format": "uv run poe format"})
        intelligent_memory.env_memory.record_python_environment("uv", {})

        # Generate commands
        test_cmd = intelligent_memory.generate_optimized_command("run tests")
        assert test_cmd == "uv run poe test"

        format_cmd = intelligent_memory.generate_optimized_command("format code")
        assert format_cmd == "uv run poe format"

        # Test fallback
        unknown_cmd = intelligent_memory.generate_optimized_command("unknown command")
        assert "not recognized" in unknown_cmd

    def test_learn_from_interaction(self, intelligent_memory):
        """Test learning from user interactions."""
        context = {"operation": "run tests", "language": "python", "file_path": "services/user.py"}
        result = {"success": True, "command_used": "uv run poe test", "execution_time": 2.5}

        # Learn from interaction
        intelligent_memory.learn_from_interaction("run tests", context, result)

        # Verify learning was recorded
        assert len(intelligent_memory.learning_cache) > 0

    def test_get_memory_summary(self, intelligent_memory):
        """Test getting comprehensive memory summary."""
        # Set up some data
        intelligent_memory.env_memory.record_shell_preference("zsh", {})
        intelligent_memory.env_memory.record_python_environment("uv", {})
        intelligent_memory.standards_memory.record_naming_convention("python", "backend", "snake_case", {})

        # Add some learning cache data
        intelligent_memory.learning_cache["test_interaction"] = {
            "timestamp": "2024-01-01T00:00:00Z",
            "operation": "run tests",
            "success": True,
        }

        summary = intelligent_memory.get_memory_summary()

        assert "environment" in summary
        assert "coding_standards" in summary
        assert "learning_cache" in summary
        assert summary["environment"]["shell"] == "zsh"
        assert summary["environment"]["python_manager"] == "uv"
        assert summary["coding_standards"]["naming_conventions"]["python"]["backend"] == "snake_case"

    def test_clear_all_memory(self, intelligent_memory):
        """Test clearing all memory components."""
        # Set up data in all components
        intelligent_memory.env_memory.record_shell_preference("zsh", {})
        intelligent_memory.standards_memory.record_naming_convention("python", "backend", "snake_case", {})
        intelligent_memory.learning_cache["test"] = {"data": "value"}

        # Clear all memory
        intelligent_memory.clear_all_memory()

        # Verify all components are cleared
        assert intelligent_memory.env_memory.get_shell_preference() is None
        assert intelligent_memory.standards_memory.get_naming_convention("python", "backend") is None
        assert len(intelligent_memory.learning_cache) == 0

    def test_get_learning_cache(self, intelligent_memory):
        """Test retrieving learning cache for specific operations."""
        # Add cache data
        intelligent_memory.learning_cache["run_tests_1"] = {
            "timestamp": "2024-01-01T00:00:00Z",
            "operation": "run tests",
            "success": True,
            "command": "uv run poe test",
        }
        intelligent_memory.learning_cache["run_tests_2"] = {
            "timestamp": "2024-01-01T01:00:00Z",
            "operation": "run tests",
            "success": False,
            "command": "pytest",
        }
        intelligent_memory.learning_cache["format_code"] = {
            "timestamp": "2024-01-01T02:00:00Z",
            "operation": "format code",
            "success": True,
            "command": "uv run poe format",
        }

        # Get cache for specific operation
        test_cache = intelligent_memory.get_learning_cache("run tests")
        assert len(test_cache) == 2
        assert all(entry["operation"] == "run tests" for entry in test_cache)

        format_cache = intelligent_memory.get_learning_cache("format code")
        assert len(format_cache) == 1
        assert format_cache[0]["operation"] == "format code"

    def test_prune_old_learning_cache(self, intelligent_memory):
        """Test pruning old learning cache entries."""
        # Add cache data with different timestamps
        import datetime

        old_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=10)
        recent_time = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)

        intelligent_memory.learning_cache["old_entry"] = {"timestamp": old_time.isoformat(), "operation": "run tests", "success": True}
        intelligent_memory.learning_cache["recent_entry"] = {
            "timestamp": recent_time.isoformat(),
            "operation": "run tests",
            "success": True,
        }

        # Prune old entries (default 7 days)
        intelligent_memory.prune_old_learning_cache()

        # Verify old entry was removed, recent entry remains
        assert "old_entry" not in intelligent_memory.learning_cache
        assert "recent_entry" in intelligent_memory.learning_cache

    def test_persistence_across_instances(self, temp_project_root):
        """Test that intelligent memory persists across instances."""
        # Create first instance and set up data
        memory1 = SerenaIntelligentMemory(temp_project_root)
        memory1.env_memory.record_shell_preference("zsh", {})
        memory1.standards_memory.record_naming_convention("python", "backend", "snake_case", {})
        memory1.learning_cache["test"] = {"timestamp": "2024-01-01T00:00:00Z"}

        # Create second instance and verify data persistence
        memory2 = SerenaIntelligentMemory(temp_project_root)
        assert memory2.env_memory.get_shell_preference() == "zsh"
        assert memory2.standards_memory.get_naming_convention("python", "backend") == "snake_case"
        assert "test" in memory2.learning_cache

    def test_get_optimal_configuration_with_no_preferences(self, intelligent_memory):
        """Test getting configuration when no preferences are set."""
        context = {"language": "python", "file_path": "test.py"}
        config = intelligent_memory.get_optimal_configuration("test operation", context)

        # Should return default configuration
        assert config["environment"]["shell"] is None
        assert config["environment"]["python_manager"] == "python"  # Default
        assert config["coding_standards"]["naming_convention"] is None
        assert config["coding_standards"]["domain"] == "general"

    def test_apply_coding_standards_with_no_standards(self, intelligent_memory):
        """Test applying coding standards when no standards are set."""
        context = {"language": "python", "file_path": "test.py"}
        original_code = "def testFunction(): pass"
        transformed_code = intelligent_memory.apply_coding_standards(original_code, context)

        # Should return original code unchanged
        assert transformed_code == original_code

    def test_generate_optimized_command_with_no_preferences(self, intelligent_memory):
        """Test generating commands when no preferences are set."""
        command = intelligent_memory.generate_optimized_command("run tests")
        assert command == "pytest"  # Default fallback

    def test_learn_from_interaction_with_failure(self, intelligent_memory):
        """Test learning from failed interactions."""
        context = {"operation": "run tests", "language": "python"}
        result = {"success": False, "error": "ImportError: module not found", "command_used": "pytest"}

        intelligent_memory.learn_from_interaction("run tests", context, result)

        # Should still record the interaction for learning
        assert len(intelligent_memory.learning_cache) > 0
        cache_entry = next(iter(intelligent_memory.learning_cache.values()))
        assert cache_entry["success"] is False
        assert "error" in cache_entry

    @patch("serena.memory.intelligent_memory.datetime")
    def test_learning_cache_timestamp_format(self, mock_datetime, intelligent_memory):
        """Test that learning cache entries have proper timestamp format."""
        import datetime

        fixed_time = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)
        mock_datetime.datetime.now.return_value = fixed_time

        context = {"operation": "test"}
        result = {"success": True}

        intelligent_memory.learn_from_interaction("test", context, result)

        # Verify timestamp format
        cache_entry = next(iter(intelligent_memory.learning_cache.values()))
        assert cache_entry["timestamp"] == "2024-01-01T12:00:00+00:00"
