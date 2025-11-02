"""Tests for ToolExecutionEngine core functionality."""

from unittest.mock import Mock

import pytest

from evolvai.core.execution import ToolExecutionEngine
from serena.tools.tools_base import Tool


class MockTool(Tool):
    """Mock tool for testing."""

    def apply(self, test_arg: str) -> str:
        """Mock apply method.

        :param test_arg: Test argument
        :return: Test result
        """
        return f"result: {test_arg}"


class TestToolExecutionEngine:
    """Test ToolExecutionEngine core functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock SerenaAgent."""
        agent = Mock()
        agent.serena_config = Mock()
        agent.serena_config.tool_timeout = 60
        agent._active_project = Mock()
        agent.is_using_language_server = Mock(return_value=False)
        return agent

    @pytest.fixture
    def mock_tool(self, mock_agent):
        """Create mock tool."""
        return MockTool(mock_agent)

    @pytest.fixture
    def engine(self, mock_agent):
        """Create ToolExecutionEngine instance."""
        return ToolExecutionEngine(agent=mock_agent)

    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert engine._constraints_enabled is False
        assert engine._audit_log == []

    def test_engine_with_constraints_enabled(self, mock_agent):
        """Test engine with constraints enabled."""
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)
        assert engine._constraints_enabled is True

    def test_execute_basic_tool(self, engine, mock_tool):
        """Test basic tool execution."""
        result = engine.execute(mock_tool, test_arg="hello")

        assert result == "result: hello"
        assert len(engine._audit_log) == 1

    def test_execute_creates_context(self, engine, mock_tool):
        """Test that execution creates proper context."""
        engine.execute(mock_tool, test_arg="test")

        audit_record = engine._audit_log[0]
        assert audit_record["tool"] == "mock"
        assert audit_record["success"] is True

    def test_execute_tracks_phases(self, engine, mock_tool):
        """Test that execution goes through all phases."""
        # This will be tested via audit log
        result = engine.execute(mock_tool, test_arg="test")

        # Should have gone through all phases successfully
        assert result == "result: test"

    def test_execute_handles_exceptions(self, engine, mock_agent):
        """Test exception handling during execution."""

        class ErrorTool(Tool):
            def apply(self) -> str:
                """Apply method that raises."""
                raise ValueError("Test error")

        error_tool = ErrorTool(mock_agent)
        result = engine.execute(error_tool)

        # Should catch exception and return error message
        assert "Error" in result or "error" in result.lower()

        # Audit log should show failure
        audit_record = engine._audit_log[0]
        assert audit_record["success"] is False

    def test_execute_with_execution_plan(self, engine, mock_tool):
        """Test execution with ExecutionPlan."""
        plan = {"steps": ["analyze", "execute"]}
        result = engine.execute(mock_tool, execution_plan=plan, test_arg="test")

        assert result == "result: test"
        # Plan should be in audit record
        # (Will verify this in integration tests)
