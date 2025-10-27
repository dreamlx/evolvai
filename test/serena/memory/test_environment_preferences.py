"""
Tests for EnvironmentPreferenceMemory component.

Tests environment preference learning, storage, and retrieval functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from serena.memory.environment_preferences import EnvironmentPreferenceMemory


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def env_memory(temp_project_root):
    """Create an EnvironmentPreferenceMemory instance for testing."""
    return EnvironmentPreferenceMemory(temp_project_root)


class TestEnvironmentPreferenceMemory:
    """Test cases for EnvironmentPreferenceMemory."""

    def test_init_creates_memory_directory(self, env_memory, temp_project_root):
        """Test that initialization creates the memory directory."""
        memory_dir = temp_project_root / ".serena" / "memory" / "environment"
        assert memory_dir.exists()
        assert memory_dir.is_dir()

    def test_record_shell_preference(self, env_memory):
        """Test recording shell preferences."""
        env_memory.record_shell_preference("zsh", {"run_test": "uv run poe test"})

        # Check that shell preference was saved
        shell_pref = env_memory.get_shell_preference()
        assert shell_pref == "zsh"

        # Check that effective commands were saved
        commands = env_memory.get_effective_commands()
        assert commands["run_test"] == "uv run poe test"

    def test_record_python_environment(self, env_memory):
        """Test recording Python environment preferences."""
        env_memory.record_python_environment("uv", {"version": "0.5.0"})

        python_manager = env_memory.get_python_manager()
        assert python_manager == "uv"

        config = env_memory.get_python_config()
        assert config["version"] == "0.5.0"

    def test_record_node_environment(self, env_memory):
        """Test recording Node.js environment preferences."""
        env_memory.record_node_environment("npm", "vite")

        node_config = env_memory.get_node_config()
        assert node_config["package_manager"] == "npm"
        assert node_config["build_tool"] == "vite"

    def test_record_container_runtime(self, env_memory):
        """Test recording container runtime preferences."""
        env_memory.record_container_runtime("docker", {"version": "24.0.0"})

        runtime = env_memory.get_container_runtime()
        assert runtime == "docker"

    def test_get_optimal_command_for_intent(self, env_memory):
        """Test getting optimal commands for specific intents."""
        # Set up environment preferences
        env_memory.record_shell_preference("zsh", {
            "run_test": "uv run poe test",
            "format": "uv run poe format",
            "type_check": "uv run poe type-check"
        })
        env_memory.record_python_environment("uv", {})

        # Test command generation
        test_cmd = env_memory.get_optimal_command_for_intent("run tests")
        assert test_cmd == "uv run poe test"

        format_cmd = env_memory.get_optimal_command_for_intent("format code")
        assert format_cmd == "uv run poe format"

        # Test fallback for unknown intent
        unknown_cmd = env_memory.get_optimal_command_for_intent("unknown command")
        assert unknown_cmd == "# Command for 'unknown command' not recognized"

    def test_get_environment_summary(self, env_memory):
        """Test getting comprehensive environment summary."""
        # Set up various preferences
        env_memory.record_shell_preference("bash", {"run_test": "poe test"})
        env_memory.record_python_environment("poetry", {"version": "1.8.0"})
        env_memory.record_node_environment("yarn", "webpack")
        env_memory.record_container_runtime("docker", {"version": "24.0.0"})

        summary = env_memory.get_environment_summary()

        assert summary["shell"]["type"] == "bash"
        assert summary["python"]["manager"] == "poetry"
        assert summary["python"]["version"] == "1.8.0"
        assert summary["nodejs"]["package_manager"] == "yarn"
        assert summary["nodejs"]["build_tool"] == "webpack"
        assert summary["container"]["runtime"] == "docker"
        assert summary["container"]["version"] == "24.0.0"

    def test_clear_environment_memory(self, env_memory):
        """Test clearing environment memory."""
        # Set up some preferences
        env_memory.record_shell_preference("zsh", {"run_test": "uv run poe test"})
        env_memory.record_python_environment("uv", {})

        # Verify preferences exist
        assert env_memory.get_shell_preference() == "zsh"
        assert env_memory.get_python_manager() == "uv"

        # Clear memory
        env_memory.clear_memory()

        # Verify preferences are cleared
        assert env_memory.get_shell_preference() is None
        assert env_memory.get_python_manager() is None

    def test_persistence_across_instances(self, temp_project_root):
        """Test that preferences persist across memory instances."""
        # Create first instance and record preferences
        env_memory1 = EnvironmentPreferenceMemory(temp_project_root)
        env_memory1.record_shell_preference("zsh", {"run_test": "uv run poe test"})
        env_memory1.record_python_environment("uv", {"version": "0.5.0"})

        # Create second instance and verify preferences persisted
        env_memory2 = EnvironmentPreferenceMemory(temp_project_root)
        assert env_memory2.get_shell_preference() == "zsh"
        assert env_memory2.get_python_manager() == "uv"
        assert env_memory2.get_python_config()["version"] == "0.5.0"

    def test_handle_corrupted_preferences_file(self, env_memory):
        """Test handling of corrupted preferences file."""
        preferences_file = env_memory.preferences_file

        # Write invalid JSON to preferences file
        with open(preferences_file, "w") as f:
            f.write("invalid json content")

        # Should handle gracefully and return None for missing preferences
        assert env_memory.get_shell_preference() is None
        assert env_memory.get_python_manager() is None

    @patch('os.environ.get')
    def test_detect_shell_from_environment(self, mock_environ_get, env_memory):
        """Test shell detection from environment variables."""
        # Test zsh detection
        mock_environ_get.return_value = "/bin/zsh"
        detected_shell = env_memory._detect_shell_type()
        assert detected_shell == "zsh"

        # Test bash detection
        mock_environ_get.return_value = "/bin/bash"
        detected_shell = env_memory._detect_shell_type()
        assert detected_shell == "bash"

        # Test fish detection
        mock_environ_get.return_value = "/usr/local/bin/fish"
        detected_shell = env_memory._detect_shell_type()
        assert detected_shell == "fish"

        # Test unknown shell
        mock_environ_get.return_value = "/bin/unknown_shell"
        detected_shell = env_memory._detect_shell_type()
        assert detected_shell is None

    def test_get_effective_commands_with_no_shell(self, env_memory):
        """Test getting effective commands when no shell is set."""
        commands = env_memory.get_effective_commands()
        assert commands == {}

    def test_get_python_config_with_no_manager(self, env_memory):
        """Test getting Python config when no manager is set."""
        config = env_memory.get_python_config()
        assert config == {}

    def test_get_node_config_with_no_nodejs(self, env_memory):
        """Test getting Node.js config when no Node.js is set."""
        config = env_memory.get_node_config()
        assert config == {"package_manager": None, "build_tool": None}

    def test_get_container_config_with_no_runtime(self, env_memory):
        """Test getting container config when no runtime is set."""
        config = env_memory.get_container_config()
        assert config == {}
