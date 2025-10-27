"""Tests for audit log and TPST analysis functionality."""
from unittest.mock import Mock

import pytest

from evolvai.core.execution import ToolExecutionEngine
from serena.tools.tools_base import Tool


class MockTool(Tool):
    """Mock tool for testing."""

    def apply(self, test_arg: str = "default") -> str:
        """Mock apply method."""
        return f"result: {test_arg}"


class TestPostExecutionPhase:
    """Test Post-execution phase implementation."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock SerenaAgent."""
        agent = Mock()
        agent.serena_config = Mock()
        agent._active_project = Mock()
        agent.is_using_language_server = Mock(return_value=False)
        agent.tool_is_active = Mock(return_value=True)
        agent.language_server = None
        agent.record_tool_usage_if_enabled = Mock()
        return agent

    @pytest.fixture
    def engine(self, mock_agent):
        """Create ToolExecutionEngine instance."""
        return ToolExecutionEngine(agent=mock_agent)

    def test_post_execution_records_tool_usage(self, engine, mock_agent):
        """Test that post-execution records tool usage."""
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        assert result == "result: test"
        # Should record tool usage
        mock_agent.record_tool_usage_if_enabled.assert_called_once()

    def test_post_execution_saves_lsp_cache(self, engine, mock_agent):
        """Test that post-execution saves LSP cache if available."""
        mock_agent.language_server = Mock()
        mock_agent.language_server.save_cache = Mock()
        tool = MockTool(mock_agent)

        result = engine.execute(tool, test_arg="test")

        assert result == "result: test"
        # Should save LSP cache
        mock_agent.language_server.save_cache.assert_called_once()


class TestAuditLogInterface:
    """Test audit log interface."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock SerenaAgent."""
        agent = Mock()
        agent.serena_config = Mock()
        agent._active_project = Mock()
        agent.is_using_language_server = Mock(return_value=False)
        agent.tool_is_active = Mock(return_value=True)
        agent.record_tool_usage_if_enabled = Mock()
        return agent

    @pytest.fixture
    def engine(self, mock_agent):
        """Create ToolExecutionEngine instance."""
        return ToolExecutionEngine(agent=mock_agent)

    def test_get_audit_log_returns_all_records(self, engine, mock_agent):
        """Test that get_audit_log returns all execution records."""
        tool = MockTool(mock_agent)

        engine.execute(tool, test_arg="test1")
        engine.execute(tool, test_arg="test2")

        audit_log = engine.get_audit_log()
        assert len(audit_log) == 2
        assert audit_log[0]["tool"] == "mock"
        assert audit_log[1]["tool"] == "mock"

    def test_get_audit_log_with_filter(self, engine, mock_agent):
        """Test that get_audit_log can filter by tool name."""
        tool = MockTool(mock_agent)

        engine.execute(tool, test_arg="test")

        audit_log = engine.get_audit_log(tool_name="mock")
        assert len(audit_log) == 1
        assert audit_log[0]["tool"] == "mock"

        audit_log = engine.get_audit_log(tool_name="nonexistent")
        assert len(audit_log) == 0

    def test_clear_audit_log(self, engine, mock_agent):
        """Test that clear_audit_log clears the log."""
        tool = MockTool(mock_agent)

        engine.execute(tool, test_arg="test")
        assert len(engine._audit_log) == 1

        engine.clear_audit_log()
        assert len(engine._audit_log) == 0


class TestTPSTAnalysis:
    """Test TPST analysis functionality."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock SerenaAgent."""
        agent = Mock()
        agent.serena_config = Mock()
        agent._active_project = Mock()
        agent.is_using_language_server = Mock(return_value=False)
        agent.tool_is_active = Mock(return_value=True)
        agent.record_tool_usage_if_enabled = Mock()
        return agent

    @pytest.fixture
    def engine(self, mock_agent):
        """Create ToolExecutionEngine instance."""
        return ToolExecutionEngine(agent=mock_agent)

    def test_analyze_tpst_returns_statistics(self, engine, mock_agent):
        """Test that analyze_tpst returns token statistics."""
        tool = MockTool(mock_agent)

        engine.execute(tool, test_arg="test")

        stats = engine.analyze_tpst()
        assert "total_executions" in stats
        assert "total_tokens" in stats
        assert "average_tokens" in stats
        assert stats["total_executions"] == 1
        assert stats["total_tokens"] > 0

    def test_get_slow_tools_identifies_slow_executions(self, engine, mock_agent):
        """Test that get_slow_tools identifies slow tool executions."""
        import time

        class SlowTool(Tool):
            def apply(self) -> str:
                time.sleep(0.02)
                return "slow_result"

        tool = SlowTool(mock_agent)

        engine.execute(tool)

        slow_tools = engine.get_slow_tools(threshold_seconds=0.01)
        assert len(slow_tools) == 1
        assert slow_tools[0]["tool"] == "slow"
        assert slow_tools[0]["duration"] > 0.01

    def test_get_token_wasters_identifies_high_token_tools(self, engine, mock_agent):
        """Test that analyze finds high token consuming tools."""
        tool = MockTool(mock_agent)

        # Execute multiple times
        engine.execute(tool, test_arg="x" * 1000)

        stats = engine.analyze_tpst()
        assert stats["average_tokens"] > 0
