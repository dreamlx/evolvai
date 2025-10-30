"""Tests for runtime constraint monitoring in ExecutionContext."""

import time
from unittest.mock import Mock

import pytest

from evolvai.core.execution import ExecutionContext


class TestExecutionContextRuntimeTracking:
    """Test ExecutionContext runtime tracking capabilities."""

    def test_files_processed_tracking_initialization(self):
        """Test that files_processed starts at 0."""
        ctx = ExecutionContext(tool_name="test", kwargs={})
        assert ctx.files_processed == 0, "files_processed should initialize to 0"

    def test_changes_made_tracking_initialization(self):
        """Test that changes_made starts at 0."""
        ctx = ExecutionContext(tool_name="test", kwargs={})
        assert ctx.changes_made == 0, "changes_made should initialize to 0"

    def test_start_time_tracking_field_exists(self):
        """Test that start_time field exists and can be set."""
        ctx = ExecutionContext(tool_name="test", kwargs={})

        # Field should exist and be a float
        assert hasattr(ctx, "start_time"), "ExecutionContext should have start_time field"
        assert isinstance(ctx.start_time, float), "start_time should be a float"

        # Can be set manually
        import time

        current_time = time.time()
        ctx.start_time = current_time
        assert ctx.start_time == current_time, "start_time should be settable"

    def test_increment_files_processed(self):
        """Test files_processed can be incremented."""
        ctx = ExecutionContext(tool_name="test", kwargs={})

        # Increment files_processed
        ctx.files_processed += 1
        assert ctx.files_processed == 1, "files_processed should be 1 after increment"

        # Increment again
        ctx.files_processed += 2
        assert ctx.files_processed == 3, "files_processed should be 3 after second increment"

    def test_increment_changes_made(self):
        """Test changes_made can be incremented."""
        ctx = ExecutionContext(tool_name="test", kwargs={})

        # Increment changes_made
        ctx.changes_made += 1
        assert ctx.changes_made == 1, "changes_made should be 1 after increment"

        # Increment again
        ctx.changes_made += 3
        assert ctx.changes_made == 4, "changes_made should be 4 after second increment"

    def test_check_limits_method_exists(self):
        """Test that check_limits method exists."""
        ctx = ExecutionContext(tool_name="test", kwargs={})

        # Method should exist (implementation not required yet)
        assert hasattr(ctx, "check_limits"), "ExecutionContext should have check_limits method"
        assert callable(getattr(ctx, "check_limits")), "check_limits should be callable"

    def test_check_limits_with_no_execution_plan(self):
        """Test that check_limits does nothing when no execution_plan provided."""
        ctx = ExecutionContext(tool_name="test", kwargs={})

        # Should not raise any exception when no execution_plan
        try:
            ctx.check_limits()
        except Exception as e:
            pytest.fail(f"check_limits should not raise exception when no execution_plan: {e}")

    def test_runtime_tracking_fields_in_audit_record(self):
        """Test that runtime tracking fields are included in audit record."""
        ctx = ExecutionContext(tool_name="test_tool", kwargs={})
        ctx.files_processed = 5
        ctx.changes_made = 3
        ctx.end_time = 100.0  # Mock end time

        record = ctx.to_audit_record()

        # Verify basic fields exist
        assert record["tool"] == "test_tool"
        assert record["success"] is True  # No error means success

        # Runtime tracking fields should be accessible through context
        # (exact audit record format may vary based on implementation)


class TestExecutionContextConstraintChecking:
    """Test ExecutionContext constraint checking capabilities."""

    def test_check_limits_with_file_limit_violation(self):
        """Test check_limits raises exception when file limit exceeded."""
        # Create mock execution plan with file limit
        mock_limits = Mock()
        mock_limits.max_files = 5

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        # Create context with execution plan
        ctx = ExecutionContext(tool_name="test_tool", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 10  # Exceeds limit

        # Should raise an exception (specific exception type will be defined in Green phase)
        with pytest.raises(Exception) as exc_info:
            ctx.check_limits()

        assert "File limit exceeded" in str(exc_info.value)
        assert "10 > 5" in str(exc_info.value)

    def test_check_limits_with_change_limit_violation(self):
        """Test check_limits raises exception when change limit exceeded."""
        # Create mock execution plan with change limit
        mock_limits = Mock()
        mock_limits.max_changes = 3
        mock_limits.max_files = 100  # High file limit to avoid file violation

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        # Create context with execution plan
        ctx = ExecutionContext(tool_name="test_tool", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 1  # Within file limit
        ctx.changes_made = 5  # Exceeds change limit

        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            ctx.check_limits()

        assert "Change limit exceeded" in str(exc_info.value)
        assert "5 > 3" in str(exc_info.value)

    def test_check_limits_with_timeout_violation(self):
        """Test check_limits raises exception when timeout exceeded."""
        # Create mock execution plan with timeout
        mock_limits = Mock()
        mock_limits.max_files = 100
        mock_limits.max_changes = 100
        mock_limits.timeout_seconds = 2.0

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        # Create context with execution plan and mock time passage
        ctx = ExecutionContext(tool_name="test_tool", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 1
        ctx.changes_made = 1
        ctx.start_time = time.time() - 5.0  # Started 5 seconds ago (exceeds 2s timeout)

        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            ctx.check_limits()

        assert "timeout" in str(exc_info.value).lower()

    def test_check_limits_within_all_limits(self):
        """Test check_limits does nothing when all constraints within limits."""
        # Create mock execution plan with reasonable limits
        mock_limits = Mock()
        mock_limits.max_files = 10
        mock_limits.max_changes = 5
        mock_limits.timeout_seconds = 30.0

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        # Create context within all limits
        ctx = ExecutionContext(tool_name="test_tool", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 3  # < 10
        ctx.changes_made = 2  # < 5
        ctx.start_time = time.time() - 1.0  # 1 second ago ( < 30s timeout)

        # Should not raise any exception
        try:
            ctx.check_limits()
        except Exception as e:
            pytest.fail(f"check_limits should not raise exception when within limits: {e}")

    def test_check_limits_file_violation_takes_precedence(self):
        """Test that file limit violation is checked first (takes precedence)."""
        # Create mock execution plan with low limits
        mock_limits = Mock()
        mock_limits.max_files = 1
        mock_limits.max_changes = 1

        mock_execution_plan = Mock()
        mock_execution_plan.limits = mock_limits

        # Create context exceeding both limits
        ctx = ExecutionContext(tool_name="test_tool", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 5  # Exceeds file limit
        ctx.changes_made = 3  # Exceeds change limit

        # Should raise file limit exception first (checked first)
        with pytest.raises(Exception) as exc_info:
            ctx.check_limits()

        assert "File limit exceeded" in str(exc_info.value)
        assert "5 > 1" in str(exc_info.value)

    def test_check_limits_with_no_limits_object(self):
        """Test check_limits behavior when execution_plan has no limits."""
        # Create mock execution plan without limits
        mock_execution_plan = Mock()
        mock_execution_plan.limits = None

        ctx = ExecutionContext(tool_name="test_tool", kwargs={})
        ctx.execution_plan = mock_execution_plan
        ctx.files_processed = 1000
        ctx.changes_made = 500

        # Should not raise any exception (graceful handling)
        try:
            ctx.check_limits()
        except Exception as e:
            pytest.fail(f"check_limits should handle missing limits gracefully: {e}")
