"""Tests for execution phase implementations."""
from unittest.mock import Mock

import pytest

from evolvai.core.execution import ToolExecutionEngine
from serena.tools.tools_base import Tool, ToolMarkerDoesNotRequireActiveProject


class MockTool(Tool):
    """Mock tool for testing."""

    def apply(self, test_arg: str = "default") -> str:
        """Mock apply method."""
        return f"result: {test_arg}"


class MockToolNoProject(Tool, ToolMarkerDoesNotRequireActiveProject):
    """Mock tool that doesn't require project."""

    def apply(self) -> str:
        """Mock apply method."""
        return "no_project_result"


class TestPreValidationPhase:
    """Test Pre-validation phase implementation."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock SerenaAgent."""
        agent = Mock()
        agent.serena_config = Mock()
        agent.serena_config.tool_timeout = 60
        agent.serena_config.project_names = ["project1", "project2"]
        agent._active_project = Mock()
        agent._active_project.project_root = "/test/project"
        agent.is_using_language_server = Mock(return_value=False)
        agent.is_language_server_running = Mock(return_value=False)
        agent.tool_is_active = Mock(return_value=True)
        agent.get_active_tool_names = Mock(return_value=["mock_tool"])
        return agent

    @pytest.fixture
    def engine(self, mock_agent):
        """Create ToolExecutionEngine instance."""
        return ToolExecutionEngine(agent=mock_agent)

    def test_tool_activation_check_passes(self, engine, mock_agent):
        """Test that tool activation check passes for active tools."""
        mock_agent.tool_is_active = Mock(return_value=True)
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        assert result == "result: test"

    def test_tool_activation_check_fails(self, engine, mock_agent):
        """Test that tool activation check fails for inactive tools."""
        mock_agent.tool_is_active = Mock(return_value=False)
        mock_agent.get_active_tool_names = Mock(return_value=["other_tool"])
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        assert "not active" in result.lower()
        assert "other_tool" in result

    def test_project_check_passes_when_project_exists(self, engine, mock_agent):
        """Test that project check passes when project is active."""
        mock_agent._active_project = Mock()
        mock_agent._active_project.project_root = "/test/project"
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        assert result == "result: test"

    def test_project_check_fails_when_no_project(self, engine, mock_agent):
        """Test that project check fails when no project is active."""
        mock_agent._active_project = None
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        assert "no active project" in result.lower()
        assert "project1" in result or "project2" in result

    def test_project_check_skipped_for_tools_without_marker(self, engine, mock_agent):
        """Test that project check is skipped for tools with no-project marker."""
        mock_agent._active_project = None
        tool = MockToolNoProject(mock_agent)

        result = engine.execute(tool)

        assert result == "no_project_result"

    def test_lsp_check_starts_language_server_if_needed(self, engine, mock_agent):
        """Test that LSP check starts language server if needed."""
        mock_agent.is_using_language_server = Mock(return_value=True)
        mock_agent.is_language_server_running = Mock(return_value=False)
        mock_agent.reset_language_server = Mock()
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        # Should start language server
        mock_agent.reset_language_server.assert_called_once()
        assert result == "result: test"

    def test_lsp_check_skipped_when_not_using_lsp(self, engine, mock_agent):
        """Test that LSP check is skipped when not using language server."""
        mock_agent.is_using_language_server = Mock(return_value=False)
        mock_agent.reset_language_server = Mock()
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        # Should not start language server
        mock_agent.reset_language_server.assert_not_called()
        assert result == "result: test"

    def test_lsp_check_skipped_when_already_running(self, engine, mock_agent):
        """Test that LSP check is skipped when language server already running."""
        mock_agent.is_using_language_server = Mock(return_value=True)
        mock_agent.is_language_server_running = Mock(return_value=True)
        mock_agent.reset_language_server = Mock()
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        # Should not restart language server
        mock_agent.reset_language_server.assert_not_called()
        assert result == "result: test"

    def test_validation_checks_run_in_order(self, engine, mock_agent):
        """Test that validation checks run in correct order."""
        # All checks should pass
        mock_agent.tool_is_active = Mock(return_value=True)
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        assert result == "result: test"
        # Verify checks were called
        mock_agent.tool_is_active.assert_called()
