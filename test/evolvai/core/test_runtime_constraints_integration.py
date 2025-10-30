"""Integration tests for runtime constraint monitoring with ToolExecutionEngine."""

import time
from unittest.mock import Mock, patch

import pytest

from evolvai.core.constraint_exceptions import (
    ChangeLimitExceededError,
    FileLimitExceededError,
    TimeoutError,
)
from evolvai.core.execution import ExecutionContext, ToolExecutionEngine
from evolvai.core.execution_plan import ExecutionLimits, ExecutionPlan, RollbackStrategy, RollbackStrategyType, ValidationConfig


class TestRuntimeConstraintsIntegration:
    """Test runtime constraints integration with ToolExecutionEngine."""

    def test_tool_execution_engine_with_file_limit_violation(self):
        """Test ToolExecutionEngine handles FileLimitExceededError during execution."""
        # Create mock agent
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        # Create mock tool
        tool = Mock()
        tool.get_name = Mock(return_value="test_tool")
        tool.is_active = Mock(return_value=True)

        # Mock tool function that simulates file processing
        def simulate_file_processing(**kwargs):
            # This will be called by ToolExecutionEngine._execute_tool
            return "simulated file processing result"

        tool.get_apply_fn = Mock(return_value=simulate_file_processing)

        # Create real execution plan with file limit
        limits = ExecutionLimits(max_files=5, max_changes=100, timeout_seconds=30.0)
        rollback = RollbackStrategy(strategy=RollbackStrategyType.MANUAL, commands=["echo 'Manual rollback needed'"])
        validation = ValidationConfig(pre_conditions=["Test condition"], expected_outcomes=["Test outcome"])

        execution_plan = ExecutionPlan(
            description="Test file processing", tool_name="test_tool", limits=limits, rollback=rollback, validation=validation
        )

        # Create execution engine with constraints enabled
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Mock the execution context to simulate file limit violation
        def mock_execute_with_violation(tool_obj, ctx):
            # Simulate file processing that exceeds limit
            ctx.files_processed = 10  # Exceeds limit of 5
            ctx.check_limits()  # Should raise FileLimitExceededError
            return "success"

        with patch.object(engine, "_execute_tool", side_effect=mock_execute_with_violation):
            # Should raise FileLimitExceededError during execution
            with pytest.raises(FileLimitExceededError) as exc_info:
                engine.execute(tool, execution_plan=execution_plan)

            assert "File limit exceeded" in str(exc_info.value)
            assert exc_info.value.files_processed == 10
            assert exc_info.value.max_files == 5

            # Verify audit log records the violation
            audit_log = engine.get_audit_log()
            assert len(audit_log) == 1
            assert audit_log[0]["tool"] == "test_tool"
            assert audit_log[0]["success"] is False

    def test_tool_execution_engine_with_change_limit_violation(self):
        """Test ToolExecutionEngine handles ChangeLimitExceededError during execution."""
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        tool = Mock()
        tool.get_name = Mock(return_value="edit_tool")
        tool.is_active = Mock(return_value=True)

        def simulate_edit_processing(**kwargs):
            ctx = kwargs.get("_context")
            if ctx:
                ctx.files_processed = 2  # Within limit
                ctx.changes_made = 8  # Exceeds limit of 5
                ctx.check_limits()  # Should raise ChangeLimitExceededError
            return "success"

        tool.get_apply_fn = Mock(return_value=simulate_edit_processing)

        mock_limits = Mock()
        mock_limits.max_files = 10
        mock_limits.max_changes = 5
        mock_limits.timeout_seconds = 30.0

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        with pytest.raises(ChangeLimitExceededError) as exc_info:
            engine.execute(tool, execution_plan=mock_execution_plan)

        assert "Change limit exceeded" in str(exc_info.value)
        assert exc_info.value.changes_made == 8
        assert exc_info.value.max_changes == 5

    @patch("time.time")
    def test_tool_execution_engine_with_timeout_violation(self, mock_time):
        """Test ToolExecutionEngine handles TimeoutError during execution."""
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        tool = Mock()
        tool.get_name = Mock(return_value="slow_tool")
        tool.is_active = Mock(return_value=True)

        def simulate_slow_processing(**kwargs):
            ctx = kwargs.get("_context")
            if ctx:
                ctx.files_processed = 1
                ctx.changes_made = 1
                # Mock time progression to simulate timeout
                mock_time.side_effect = [0, 5]  # Start at 0, check at 5 seconds
                ctx.check_limits()  # Should raise TimeoutError (5s > 2s)
            return "success"

        tool.get_apply_fn = Mock(return_value=simulate_slow_processing)

        mock_limits = Mock()
        mock_limits.max_files = 10
        mock_limits.max_changes = 10
        mock_limits.timeout_seconds = 2.0

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        with pytest.raises(TimeoutError) as exc_info:
            engine.execute(tool, execution_plan=mock_execution_plan)

        assert "timeout" in str(exc_info.value).lower()
        assert exc_info.value.timeout_seconds == 2.0
        assert exc_info.value.elapsed_time == 5.0

    def test_tool_execution_engine_within_constraints(self):
        """Test ToolExecutionEngine executes successfully when within constraints."""
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        tool = Mock()
        tool.get_name = Mock(return_value="normal_tool")
        tool.is_active = Mock(return_value=True)

        def simulate_normal_processing(**kwargs):
            ctx = kwargs.get("_context")
            if ctx:
                ctx.files_processed = 3  # < 10
                ctx.changes_made = 2  # < 5
                ctx.check_limits()  # Should not raise
            return "operation completed successfully"

        tool.get_apply_fn = Mock(return_value=simulate_normal_processing)

        mock_limits = Mock()
        mock_limits.max_files = 10
        mock_limits.max_changes = 5
        mock_limits.timeout_seconds = 30.0

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Should execute successfully without raising exceptions
        result = engine.execute(tool, execution_plan=mock_execution_plan)
        assert result == "operation completed successfully"

        # Verify audit log records successful execution
        audit_log = engine.get_audit_log()
        assert len(audit_log) == 1
        assert audit_log[0]["tool"] == "normal_tool"
        assert audit_log[0]["success"] is True

    def test_tool_execution_engine_constraints_disabled(self):
        """Test ToolExecutionEngine ignores constraints when disabled."""
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        tool = Mock()
        tool.get_name = Mock(return_value="unconstrained_tool")
        tool.is_active = Mock(return_value=True)

        def simulate_processing_without_constraints(**kwargs):
            # Even with excessive values, should not raise when constraints disabled
            return "success without constraints"

        tool.get_apply_fn = Mock(return_value=simulate_processing_without_constraints)

        mock_limits = Mock()
        mock_limits.max_files = 1  # Very low limit
        mock_limits.max_changes = 1
        mock_limits.timeout_seconds = 0.001  # Very short timeout

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        # Create engine with constraints DISABLED
        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=False)

        # Should execute successfully even with execution_plan that has strict limits
        result = engine.execute(tool, execution_plan=mock_execution_plan)
        assert result == "success without constraints"

    def test_tool_execution_engine_no_execution_plan(self):
        """Test ToolExecutionEngine works normally without execution_plan."""
        mock_agent = Mock()
        mock_agent._active_project = Mock()
        mock_agent.is_using_language_server = Mock(return_value=False)

        tool = Mock()
        tool.get_name = Mock(return_value="legacy_tool")
        tool.is_active = Mock(return_value=True)
        tool.get_apply_fn = Mock(return_value="legacy operation completed")

        engine = ToolExecutionEngine(agent=mock_agent, enable_constraints=True)

        # Should execute successfully without execution_plan (backward compatibility)
        result = engine.execute(tool)
        assert result == "legacy operation completed"

        # Verify audit log records execution
        audit_log = engine.get_audit_log()
        assert len(audit_log) == 1
        assert audit_log[0]["tool"] == "legacy_tool"
        assert audit_log[0]["success"] is True


class TestPerformanceConstraints:
    """Test performance characteristics of runtime constraint checking."""

    def test_check_limits_performance_under_2ms(self):
        """Test that check_limits() runs in under 2ms."""
        # Create context with execution plan
        mock_limits = Mock()
        mock_limits.max_files = 100
        mock_limits.max_changes = 50
        mock_limits.timeout_seconds = 30.0

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        ctx = ExecutionContext(tool_name="performance_test", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 25
        ctx.changes_made = 12
        ctx.start_time = time.time()  # Set realistic start time to avoid timeout

        # Measure execution time
        start_time = time.perf_counter()
        for _ in range(1000):  # Run multiple times for average
            ctx.check_limits()  # Should not raise
        end_time = time.perf_counter()

        average_time_ms = (end_time - start_time) / 1000 * 1000

        # Should be well under 2ms target
        assert average_time_ms < 1.0, f"check_limits() took {average_time_ms:.3f}ms on average"

    def test_constraint_checking_overhead_minimal(self):
        """Test that constraint checking adds minimal overhead."""
        mock_limits = Mock()
        mock_limits.max_files = 1000
        mock_limits.max_changes = 500
        mock_limits.timeout_seconds = 300.0

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        ctx = ExecutionContext(tool_name="overhead_test", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 100
        ctx.changes_made = 50
        ctx.start_time = time.time()  # Set realistic start time

        # Time constraint checking
        start_time = time.perf_counter()
        for _ in range(10000):
            ctx.check_limits()
        constraint_time = time.perf_counter() - start_time

        # Time simple operation (baseline)
        start_time = time.perf_counter()
        for _ in range(10000):
            pass  # No operation
        baseline_time = time.perf_counter() - start_time

        overhead_ms = (constraint_time - baseline_time) * 1000

        # Overhead should be minimal (<0.5ms per check for 10000 checks = 0.00005ms per check)
        assert overhead_ms < 5.0, f"Constraint checking overhead: {overhead_ms:.3f}ms for 10000 checks"
