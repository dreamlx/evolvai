"""
Tests for Intelligent Tools.

Tests environment detection, optimized command generation, and tool optimization.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from serena.agent import SerenaAgent
from serena.config.serena_config import ProjectConfig
from serena.project import Project
from serena.tools.intelligent_tools import DetectEnvironmentTool, GenerateOptimizedCommandTool, ShowEnvironmentPreferencesTool


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_project(temp_project_root):
    """Create a mock project for testing tools."""
    project_config = ProjectConfig(
        project_name="test_project",
        language="python",
        ignored_paths=[],
        excluded_tools=set(),
        read_only=False,
        ignore_all_files_in_gitignore=True,
        initial_prompt="",
        encoding="utf-8"
    )
    return Project(project_root=str(temp_project_root), project_config=project_config)


@pytest.fixture
def mock_agent(mock_project):
    """Create a mock Serena agent."""
    agent = Mock(spec=SerenaAgent)
    agent.project = mock_project
    agent.serena_config = Mock()
    agent.serena_config.default_max_tool_answer_chars = 10000
    return agent


class TestDetectEnvironmentTool:
    """Test cases for DetectEnvironmentTool."""

    @pytest.fixture
    def detect_tool(self, mock_agent):
        """Create DetectEnvironmentTool instance."""
        return DetectEnvironmentTool(mock_agent)

    @patch('os.environ.get')
    @patch('shutil.which')
    def test_detect_zsh_environment(self, mock_which, mock_environ_get, detect_tool, temp_project_root):
        """Test detecting zsh environment with uv."""
        # Setup environment
        mock_environ_get.return_value = "/bin/zsh"
        mock_which.return_value = "/usr/local/bin/docker"

        # Create uv.lock file to simulate uv environment
        (temp_project_root / "uv.lock").touch()

        result = detect_tool.apply()
        result_data = json.loads(result)

        assert result_data["status"] == "Environment preferences recorded"
        assert result_data["detected"]["shell"] == "zsh"
        assert result_data["detected"]["python_manager"] == "uv"
        assert result_data["detected"]["container_runtime"] == "docker"

    @patch('os.environ.get')
    @patch('shutil.which')
    def test_detect_bash_environment(self, mock_which, mock_environ_get, detect_tool, temp_project_root):
        """Test detecting bash environment with poetry."""
        # Setup environment
        mock_environ_get.return_value = "/bin/bash"
        mock_which.return_value = None

        # Create poetry.lock file to simulate poetry environment
        (temp_project_root / "poetry.lock").touch()

        result = detect_tool.apply()
        result_data = json.loads(result)

        assert result_data["status"] == "Environment preferences recorded"
        assert result_data["detected"]["shell"] == "bash"
        assert result_data["detected"]["python_manager"] == "poetry"

    @patch('os.environ.get')
    def test_detect_node_environment(self, mock_environ_get, detect_tool, temp_project_root):
        """Test detecting Node.js environment."""
        # Setup environment
        mock_environ_get.return_value = "/bin/zsh"

        # Create package.json and yarn.lock
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {"react": "^18.0.0"}
        }
        (temp_project_root / "package.json").write_text(json.dumps(package_json))
        (temp_project_root / "yarn.lock").touch()
        (temp_project_root / "vite.config.js").touch()

        result = detect_tool.apply()
        result_data = json.loads(result)

        assert result_data["detected"]["package_manager"] == "yarn"
        assert result_data["detected"]["build_tool"] == "vite"

    @patch('os.environ.get')
    def test_detect_unknown_shell(self, mock_environ_get, detect_tool, temp_project_root):
        """Test detecting unknown shell."""
        # Setup environment
        mock_environ_get.return_value = "/bin/unknown_shell"

        result = detect_tool.apply()
        result_data = json.loads(result)

        assert "shell" not in result_data["detected"]

    def test_detect_no_python_manager(self, detect_tool, temp_project_root):
        """Test when no Python manager is detected."""
        result = detect_tool.apply()
        result_data = json.loads(result)

        assert result_data["detected"]["python_manager"] == "python"  # Default

    def test_detect_no_node_environment(self, detect_tool, temp_project_root):
        """Test when no Node.js environment is detected."""
        result = detect_tool.apply()
        result_data = json.loads(result)

        assert "package_manager" not in result_data["detected"]


class TestGenerateOptimizedCommandTool:
    """Test cases for GenerateOptimizedCommandTool."""

    @pytest.fixture
    def command_tool(self, mock_agent):
        """Create GenerateOptimizedCommandTool instance."""
        return GenerateOptimizedCommandTool(mock_agent)

    def test_generate_uv_test_command(self, command_tool, mock_agent, temp_project_root):
        """Test generating uv test commands."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_shell_preference("zsh", {})
        env_memory.record_python_environment("uv", {})

        result = command_tool.apply("run tests")
        result_data = json.loads(result)

        assert result_data["command"] == "uv run poe test"
        assert result_data["environment"]["shell"] == "zsh"
        assert result_data["environment"]["python_manager"] == "uv"
        assert result_data["optimization_applied"] is True

    def test_generate_poetry_test_command(self, command_tool, mock_agent, temp_project_root):
        """Test generating poetry test commands."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_shell_preference("bash", {})
        env_memory.record_python_environment("poetry", {})

        result = command_tool.apply("run tests")
        result_data = json.loads(result)

        assert result_data["command"] == "poetry run pytest"
        assert result_data["environment"]["python_manager"] == "poetry"
        assert result_data["optimization_applied"] is True

    def test_generate_format_command(self, command_tool, mock_agent, temp_project_root):
        """Test generating format commands."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_python_environment("uv", {})

        result = command_tool.apply("format code")
        result_data = json.loads(result)

        assert result_data["command"] == "uv run poe format"
        assert result_data["optimization_applied"] is True

    def test_generate_type_check_command(self, command_tool, mock_agent, temp_project_root):
        """Test generating type check commands."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_python_environment("uv", {})

        result = command_tool.apply("type checking")
        result_data = json.loads(result)

        assert result_data["command"] == "uv run poe type-check"
        assert result_data["optimization_applied"] is True

    def test_generate_build_command(self, command_tool, mock_agent, temp_project_root):
        """Test generating build commands."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_python_environment("uv", {})

        result = command_tool.apply("build project")
        result_data = json.loads(result)

        assert result_data["command"] == "uv build"
        assert result_data["optimization_applied"] is True

    def test_fallback_to_generic_command(self, command_tool, mock_agent, temp_project_root):
        """Test fallback to generic commands when no preferences."""
        result = command_tool.apply("run tests")
        result_data = json.loads(result)

        assert result_data["command"] == "pytest"  # Default fallback
        assert result_data["optimization_applied"] is False

    def test_unknown_intent_fallback(self, command_tool, mock_agent, temp_project_root):
        """Test fallback for unknown intents."""
        result = command_tool.apply("unknown operation")
        result_data = json.loads(result)

        assert "not recognized" in result_data["command"]
        assert result_data["optimization_applied"] is False

    def test_case_insensitive_intent_matching(self, command_tool, mock_agent, temp_project_root):
        """Test case-insensitive intent matching."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_python_environment("uv", {})

        # Test various case combinations
        test_cases = ["RUN TESTS", "Run Tests", "run TESTS", "test"]

        for intent in test_cases:
            result = command_tool.apply(intent)
            result_data = json.loads(result)
            assert result_data["command"] == "uv run poe test"


class TestShowEnvironmentPreferencesTool:
    """Test cases for ShowEnvironmentPreferencesTool."""

    @pytest.fixture
    def show_tool(self, mock_agent):
        """Create ShowEnvironmentPreferencesTool instance."""
        return ShowEnvironmentPreferencesTool(mock_agent)

    def test_show_empty_preferences(self, show_tool, mock_agent, temp_project_root):
        """Test showing preferences when none are set."""
        result = show_tool.apply()
        result_data = json.loads(result)

        assert "environment_preferences" in result_data
        assert result_data["environment_preferences"]["shell"]["type"] is None
        assert result_data["environment_preferences"]["python"]["manager"] == "python"  # Default

    def test_show_saved_preferences(self, show_tool, mock_agent, temp_project_root):
        """Test showing saved preferences."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_shell_preference("zsh", {"run_test": "uv run poe test"})
        env_memory.record_python_environment("uv", {"version": "0.5.0"})
        env_memory.record_node_environment("npm", "vite")
        env_memory.record_container_runtime("docker", {"version": "24.0.0"})

        result = show_tool.apply()
        result_data = json.loads(result)

        assert result_data["environment_preferences"]["shell"]["type"] == "zsh"
        assert result_data["environment_preferences"]["python"]["manager"] == "uv"
        assert result_data["environment_preferences"]["python"]["version"] == "0.5.0"
        assert result_data["environment_preferences"]["nodejs"]["package_manager"] == "npm"
        assert result_data["environment_preferences"]["nodejs"]["build_tool"] == "vite"
        assert result_data["environment_preferences"]["container"]["runtime"] == "docker"

    def test_message_in_result(self, show_tool, mock_agent, temp_project_root):
        """Test that result contains explanatory message."""
        result = show_tool.apply()
        result_data = json.loads(result)

        assert "message" in result_data
        assert "optimize AI tool commands" in result_data["message"]
