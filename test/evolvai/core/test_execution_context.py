"""Tests for ExecutionContext and ExecutionPhase."""

import time

from evolvai.core.execution import ExecutionContext, ExecutionPhase


class TestExecutionPhase:
    """Test ExecutionPhase enum."""

    def test_execution_phase_values(self):
        """Test that all expected phases exist."""
        assert ExecutionPhase.PRE_VALIDATION
        assert ExecutionPhase.PRE_EXECUTION
        assert ExecutionPhase.EXECUTION
        assert ExecutionPhase.POST_EXECUTION

    def test_execution_phase_ordering(self):
        """Test that phases have correct ordering."""
        phases = list(ExecutionPhase)
        assert phases[0] == ExecutionPhase.PRE_VALIDATION
        assert phases[1] == ExecutionPhase.PRE_EXECUTION
        assert phases[2] == ExecutionPhase.EXECUTION
        assert phases[3] == ExecutionPhase.POST_EXECUTION


class TestExecutionContext:
    """Test ExecutionContext dataclass."""

    def test_execution_context_creation(self):
        """Test basic ExecutionContext creation."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={"arg1": "value1"},
        )

        assert ctx.tool_name == "test_tool"
        assert ctx.kwargs == {"arg1": "value1"}
        assert ctx.execution_plan is None
        assert ctx.phase == ExecutionPhase.PRE_VALIDATION
        assert ctx.result is None
        assert ctx.error is None

    def test_execution_context_with_plan(self):
        """Test ExecutionContext with execution plan."""
        plan = {"steps": ["step1", "step2"]}
        ctx = ExecutionContext(tool_name="test_tool", kwargs={}, execution_plan=plan)

        assert ctx.execution_plan == plan

    def test_execution_context_timing(self):
        """Test ExecutionContext time tracking."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.start_time = time.time()
        time.sleep(0.01)  # Small delay
        ctx.end_time = time.time()

        duration = ctx.end_time - ctx.start_time
        assert duration > 0
        assert duration < 0.1  # Should be quick

    def test_execution_context_token_tracking(self):
        """Test ExecutionContext token metrics."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.estimated_tokens = 100
        ctx.actual_tokens = 95

        assert ctx.estimated_tokens == 100
        assert ctx.actual_tokens == 95

    def test_execution_context_constraint_tracking(self):
        """Test ExecutionContext constraint violation tracking."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.constraint_violations = ["violation1", "violation2"]
        ctx.should_batch = True

        assert len(ctx.constraint_violations) == 2
        assert ctx.should_batch is True

    def test_execution_context_to_audit_record(self):
        """Test conversion to audit record."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={"arg": "value"},
        )

        ctx.start_time = time.time()
        ctx.end_time = ctx.start_time + 0.5
        ctx.phase = ExecutionPhase.EXECUTION
        ctx.actual_tokens = 100
        ctx.constraint_violations = []
        ctx.should_batch = False

        record = ctx.to_audit_record()

        assert record["tool"] == "test_tool"
        assert record["phase"] == "execution"
        assert record["duration"] == 0.5
        assert record["tokens"] == 100
        assert record["success"] is True
        assert record["constraints"] == []
        assert record["batched"] is False

    def test_execution_context_to_audit_record_with_error(self):
        """Test audit record with error."""
        ctx = ExecutionContext(
            tool_name="test_tool",
            kwargs={},
        )

        ctx.start_time = time.time()
        ctx.end_time = time.time()
        ctx.error = ValueError("test error")

        record = ctx.to_audit_record()

        assert record["success"] is False
