"""
Tests for Advanced Intelligent Tools.

Tests comprehensive AI optimization, code generation, and system coordination.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from serena.agent import SerenaAgent
from serena.config.serena_config import ProjectConfig
from serena.project import Project
from serena.tools.advanced_intelligent_tools import (
    OptimizeAIToolsTool,
    GenerateOptimizedCodeTool,
    ShowIntelligentMemoryStatusTool,
    ResetIntelligentMemoryTool
)


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


class TestOptimizeAIToolsTool:
    """Test cases for OptimizeAIToolsTool."""

    @pytest.fixture
    def optimize_tool(self, mock_agent):
        """Create OptimizeAIToolsTool instance."""
        return OptimizeAIToolsTool(mock_agent)

    def test_optimize_with_uv_environment(self, optimize_tool, mock_agent, temp_project_root):
        """Test optimization with uv environment detected."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_shell_preference("zsh", {})
        env_memory.record_python_environment("uv", {})

        # Pre-set coding standards
        from serena.memory.coding_standards import CodingStandardsMemory
        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("python", "backend", "snake_case", {})

        result = optimize_tool.apply("run tests", {"language": "python"})
        result_data = json.loads(result)

        assert result_data["operation"] == "run tests"
        assert "optimal_configuration" in result_data
        assert "recommendations" in result_data
        assert result_data["message"] == "Optimized configuration generated using Serena's intelligent memory"

        config = result_data["optimal_configuration"]
        assert config["environment"]["python_manager"] == "uv"
        assert config["environment"]["shell"] == "zsh"
        assert config["coding_standards"]["naming_convention"] == "snake_case"

        recommendations = result_data["recommendations"]
        assert "environment_optimizations" in recommendations
        assert "coding_standards" in recommendations
        assert "tool_suggestions" in recommendations

    def test_optimize_with_test_operation(self, optimize_tool, mock_agent, temp_project_root):
        """Test optimization for test-related operations."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_python_environment("uv", {})

        result = optimize_tool.apply("run unit tests")
        result_data = json.loads(result)

        recommendations = result_data["recommendations"]
        test_suggestions = [rec for rec in recommendations["tool_suggestions"] if rec["type"] == "test_framework"]
        assert len(test_suggestions) > 0

    def test_optimize_with_format_operation(self, optimize_tool, mock_agent, temp_project_root):
        """Test optimization for formatting operations."""
        result = optimize_tool.apply("format code")
        result_data = json.loads(result)

        recommendations = result_data["recommendations"]
        format_suggestions = [rec for rec in recommendations["tool_suggestions"] if rec["type"] == "code_formatting"]
        assert len(format_suggestions) > 0

    def test_optimize_with_no_preferences(self, optimize_tool, mock_agent, temp_project_root):
        """Test optimization when no preferences are set."""
        result = optimize_tool.apply("test operation")
        result_data = json.loads(result)

        config = result_data["optimal_configuration"]
        assert config["environment"]["shell"] is None
        assert config["environment"]["python_manager"] == "python"  # Default
        assert config["coding_standards"]["naming_convention"] is None

    def test_generate_recommendations_with_zsh_shell(self, optimize_tool, mock_agent, temp_project_root):
        """Test recommendation generation for zsh shell."""
        # Pre-set zsh environment
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_shell_preference("zsh", {})

        result = optimize_tool.apply("test operation")
        result_data = json.loads(result)

        recommendations = result_data["recommendations"]
        shell_optimizations = [rec for rec in recommendations["environment_optimizations"] if rec["type"] == "shell_compatibility"]
        assert len(shell_optimizations) > 0
        assert "zsh-compatible" in shell_optimizations[0]["suggestion"]

    def test_generate_recommendations_with_camel_case(self, optimize_tool, mock_agent, temp_project_root):
        """Test recommendation generation for camelCase naming."""
        # Pre-set camelCase coding standards
        from serena.memory.coding_standards import CodingStandardsMemory
        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("javascript", "frontend", "camelCase", {})

        result = optimize_tool.apply("test operation", {"language": "javascript"})
        result_data = json.loads(result)

        recommendations = result_data["recommendations"]
        naming_rec = [rec for rec in recommendations["coding_standards"] if rec["type"] == "naming_convention"]
        assert len(naming_rec) > 0
        assert naming_rec[0]["convention"] == "camelCase"


class TestGenerateOptimizedCodeTool:
    """Test cases for GenerateOptimizedCodeTool."""

    @pytest.fixture
    def generate_tool(self, mock_agent):
        """Create GenerateOptimizedCodeTool instance."""
        return GenerateOptimizedCodeTool(mock_agent)

    def test_generate_python_function(self, generate_tool, mock_agent, temp_project_root):
        """Test generating optimized Python function."""
        # Pre-set coding standards
        from serena.memory.coding_standards import CodingStandardsMemory
        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("python", "backend", "snake_case", {})

        result = generate_tool.apply("create a function to validate user input", "python", "services/user.py")
        result_data = json.loads(result)

        assert result_data["request"] == "create a function to validate user input"
        assert result_data["language"] == "python"
        assert "generated_code" in result_data
        assert "applied_optimizations" in result_data

        generated_code = result_data["generated_code"]
        assert "def example_function" in generated_code  # snake_case naming applied

    def test_generate_python_class(self, generate_tool, mock_agent, temp_project_root):
        """Test generating optimized Python class."""
        result = generate_tool.apply("create a user management class", "python")
        result_data = json.loads(result)

        generated_code = result_data["generated_code"]
        assert "class ExampleClass" in generated_code

    def test_generate_javascript_function(self, generate_tool, mock_agent, temp_project_root):
        """Test generating optimized JavaScript function."""
        # Pre-set camelCase coding standards
        from serena.memory.coding_standards import CodingStandardsMemory
        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("javascript", "frontend", "camelCase", {})

        result = generate_tool.apply("create a function to fetch user data", "javascript", "frontend/utils.js")
        result_data = json.loads(result)

        generated_code = result_data["generated_code"]
        assert "function exampleFunction" in generated_code  # camelCase naming applied

    def test_generate_with_no_standards(self, generate_tool, mock_agent, temp_project_root):
        """Test generating code when no standards are set."""
        result = generate_tool.apply("create a test function", "python")
        result_data = json.loads(result)

        optimizations = result_data["applied_optimizations"]
        assert optimizations["coding_standards"]["naming_convention"] is None

    def test_learn_from_interaction(self, generate_tool, mock_agent, temp_project_root):
        """Test that tool learns from interactions."""
        result = generate_tool.apply("create a function", "python")
        result_data = json.loads(result)

        # The tool should have learned from the interaction
        # This is tested indirectly through the fact that the tool completes without error
        assert result_data["message"] == "Code generated with Serena's intelligent optimizations"

    def test_placeholder_code_generation(self, generate_tool, mock_agent, temp_project_root):
        """Test placeholder code generation for unsupported scenarios."""
        result = generate_tool.apply("create something complex", "ruby")
        result_data = json.loads(result)

        generated_code = result_data["generated_code"]
        assert "Generated code for" in generated_code
        assert "Language: ruby" in generated_code


class TestShowIntelligentMemoryStatusTool:
    """Test cases for ShowIntelligentMemoryStatusTool."""

    @pytest.fixture
    def status_tool(self, mock_agent):
        """Create ShowIntelligentMemoryStatusTool instance."""
        return ShowIntelligentMemoryStatusTool(mock_agent)

    def test_show_empty_memory_status(self, status_tool, mock_agent, temp_project_root):
        """Test showing status when no memory is stored."""
        result = status_tool.apply()
        result_data = json.loads(result)

        assert "intelligent_memory_status" in result_data
        assert "capabilities" in result_data
        assert "optimization_examples" in result_data
        assert result_data["message"] == "Serena's intelligent memory is actively optimizing AI tool usage"

    def test_show_memory_status_with_data(self, status_tool, mock_agent, temp_project_root):
        """Test showing status with stored memory data."""
        # Pre-set environment preferences
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_shell_preference("zsh", {})
        env_memory.record_python_environment("uv", {})

        # Pre-set coding standards
        from serena.memory.coding_standards import CodingStandardsMemory
        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("python", "backend", "snake_case", {})

        result = status_tool.apply()
        result_data = json.loads(result)

        status = result_data["intelligent_memory_status"]
        assert "environment" in status
        assert "coding_standards" in status
        assert "learning_cache" in status

        capabilities = result_data["capabilities"]
        assert capabilities["environment_optimization"] == "Shell, Python, Node.js preferences learned"
        assert capabilities["coding_standards"] == "Naming conventions and style preferences applied"

    def test_optimization_examples(self, status_tool, mock_agent, temp_project_root):
        """Test optimization examples in status."""
        result = status_tool.apply()
        result_data = json.loads(result)

        examples = result_data["optimization_examples"]
        assert "command_generation" in examples
        assert "code_generation" in examples
        assert "tool_selection" in examples
        assert "style_application" in examples


class TestResetIntelligentMemoryTool:
    """Test cases for ResetIntelligentMemoryTool."""

    @pytest.fixture
    def reset_tool(self, mock_agent):
        """Create ResetIntelligentMemoryTool instance."""
        return ResetIntelligentMemoryTool(mock_agent)

    def test_reset_without_confirmation(self, reset_tool, mock_agent, temp_project_root):
        """Test reset without proper confirmation."""
        result = reset_tool.apply("false")
        result_data = json.loads(result)

        assert result_data["status"] == "reset_cancelled"
        assert "confirm='true'" in result_data["message"]
        assert "warning" in result_data

    def test_reset_with_invalid_confirmation(self, reset_tool, mock_agent, temp_project_root):
        """Test reset with invalid confirmation."""
        result = reset_tool.apply("invalid")
        result_data = json.loads(result)

        assert result_data["status"] == "reset_cancelled"

    def test_reset_with_confirmation(self, reset_tool, mock_agent, temp_project_root):
        """Test successful reset with proper confirmation."""
        # Pre-set some data to verify it gets cleared
        from serena.memory.environment_preferences import EnvironmentPreferenceMemory
        env_memory = EnvironmentPreferenceMemory(temp_project_root)
        env_memory.record_shell_preference("zsh", {})

        result = reset_tool.apply("true")
        result_data = json.loads(result)

        assert result_data["status"] == "reset_completed"
        assert "cleared" in result_data["message"]
        assert "next_steps" in result_data

    def test_reset_case_insensitive(self, reset_tool, mock_agent, temp_project_root):
        """Test reset with case-insensitive confirmation."""
        result = reset_tool.apply("TRUE")
        result_data = json.loads(result)

        assert result_data["status"] == "reset_completed"

    def test_reset_warning_content(self, reset_tool, mock_agent, temp_project_root):
        """Test that reset warning contains proper information."""
        result = reset_tool.apply("false")
        result_data = json.loads(result)

        warning = result_data["warning"]
        assert "environment preferences" in warning
        assert "coding standards" in warning
        assert "learning cache" in warning